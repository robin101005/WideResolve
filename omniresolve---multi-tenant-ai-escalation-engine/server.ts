import express from 'express';
import { createServer as createViteServer } from 'vite';
import { GoogleGenAI } from '@google/genai';
import dotenv from 'dotenv';
dotenv.config();

const app = express();
const port = 3000;

app.use(express.json());

// Initialize Google GenAI with environment key
const ai = new GoogleGenAI();

// Endpoint for Gemini-powered investigation
app.post('/api/investigate', async (req, res) => {
  const startTime = Date.now();
  try {
    const {
      clientId,
      customerProfile,
      complaint,
      orderContext,
      policies
    } = req.body;

    const systemPrompt = `You are the lead AI detective for WideResolve, built for Widesoftech.
You investigate B2B client customer tickets for 3 industries:
1. QuickCart (E-commerce)
2. TeleNet (Telecom)
3. CareLink (Healthcare - strict safety: any clinical/medical symptom inquiry must be flagged immediately)

Analyze the complaint against the customer profile, order history, and relevant SLA contract clauses.
Respond with a valid JSON object ONLY (no markdown code blocks, just raw JSON) matching this exact schema:
{
  "issueType": "Double Charge" | "Outage Credit" | "Missing Delivery" | "Clinical Triage" | "General Billing" | "Service Disruption",
  "sentiment": "Angry" | "Frustrated" | "Neutral" | "Anxious",
  "urgency": "High" | "Medium" | "Low",
  "legalThreat": boolean,
  "fraudClaim": boolean,
  "medicalMention": boolean,
  "hypotheses": [
    {"hypothesis": string, "probability": number, "explanation": string}
  ],
  "rootCauseMargin": number,
  "proposedAction": string,
  "proposedAmount": number,
  "citedClause": string,
  "customerMessage": string,
  "executiveSummary": string,
  "reasoningSteps": [string]
}`;

    const userPrompt = `
CLIENT: ${clientId}
CUSTOMER PROFILE: ${JSON.stringify(customerProfile || {})}
ORDER / INCIDENT DATA: ${JSON.stringify(orderContext || {})}
CONTRACT CLAUSES AVAILABLE: ${JSON.stringify(policies || [])}
INBOUND COMPLAINT: "${complaint}"

Investigate thoroughly and return the JSON analysis.`;

    // Try primary model, fallback gracefully if upstream 503
    const candidateModels = ['gemini-3.8-flash', 'gemini-3.1-flash-lite', 'gemini-2.5-flash'];
    let geminiResp: any = null;
    let usedModel = 'gemini-3.8-flash';

    for (const modelName of candidateModels) {
      try {
        geminiResp = await ai.models.generateContent({
          model: modelName,
          contents: [
            { role: 'user', parts: [{ text: `${systemPrompt}\n\n${userPrompt}` }] }
          ]
        });
        if (geminiResp?.text) {
          usedModel = modelName;
          break;
        }
      } catch (e: any) {
        console.warn(`Model ${modelName} returned error, trying fallback...`, e.message || e);
      }
    }

    if (!geminiResp?.text) {
      throw new Error('All Gemini candidate models returned high demand / rate limits');
    }

    const responseText = geminiResp.text || '{}';
    // Clean potential markdown blocks
    const cleanJson = responseText.replace(/```json/g, '').replace(/```/g, '').trim();
    let parsedData = {};
    try {
      parsedData = JSON.parse(cleanJson);
    } catch {
      parsedData = {
        executiveSummary: responseText.slice(0, 300),
        reasoningSteps: ['Extracted direct response from Gemini model.']
      };
    }

    const durationMs = Date.now() - startTime;

    res.json({
      success: true,
      aiPowered: true,
      model: usedModel,
      latencyMs: durationMs,
      rawOutput: responseText,
      analysis: parsedData
    });
  } catch (err: any) {
    console.error('Gemini investigation error:', err);
    res.status(500).json({
      success: false,
      aiPowered: false,
      error: err.message || 'Gemini processing failed',
      latencyMs: Date.now() - startTime
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'online',
    system: 'WideResolve',
    aiModel: 'gemini-3.8-flash',
    geminiKeyConfigured: !!process.env.GEMINI_API_KEY
  });
});

async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    // Mount Vite dev server middleware
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa'
    });
    app.use(vite.middlewares);
  } else {
    // Production static serve
    app.use(express.static('dist'));
  }

  app.listen(port, '0.0.0.0', () => {
    console.log(`WideResolve server listening on http://0.0.0.0:${port}`);
    console.log(`Gemini AI active: gemini-3.8-flash`);
  });
}

startServer();
