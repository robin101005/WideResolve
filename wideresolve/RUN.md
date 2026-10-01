# Run WideResolve

1. Install: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and paste your Anthropic API key (get one at console.anthropic.com). Never commit `.env`.
3. Check the logic: `python run_tests.py` (6 sample tickets, works without a key)
4. Start the app: `streamlit run app.py`

No key? The app still runs in offline mode with rule-based intent and template replies.
Regenerate the simulated data any time: `python build_data.py`
