"""
Tenant-Isolated Policy Search (RAG) Engine for OmniResolve.
Splits markdown policies by clause with client_id metadata.
Implements hybrid retrieval (keyword BM25 + dense token vector cosine similarity).
Enforces zero cross-tenant leakage.
"""

import os
import re
import math
from typing import List, Dict, Any, Optional

POLICIES_DIR = os.path.join(os.path.dirname(__file__), "..", "policies")

class PolicyClause:
    def __init__(self, client_id: str, clause_id: str, title: str, text: str, citation: str):
        self.client_id = client_id.lower()
        self.clause_id = clause_id
        self.title = title
        self.text = text
        self.citation = citation
        self.tokens = self._tokenize(f"{clause_id} {title} {text}")

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [w.lower() for w in re.findall(r'\b[a-zA-Z0-9§\.\-]+\b', text)]

class PolicyRAG:
    def __init__(self, policies_dir: str = POLICIES_DIR):
        self.policies_dir = policies_dir
        self.clauses: List[PolicyClause] = []
        self.idf: Dict[str, float] = {}
        self.load_policies()

    def load_policies(self):
        """Parse all markdown files in policies/ and build indexed corpus."""
        self.clauses = []
        policy_files = {
            "quickcart": "quickcart_policies.md",
            "telenet": "telenet_policies.md",
            "carelink": "carelink_policies.md"
        }

        for client_id, filename in policy_files.items():
            filepath = os.path.join(self.policies_dir, filename)
            if not os.path.exists(filepath):
                continue
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract bullet points like: - **Refund §1.1**: Double Charges — Description...
            pattern = re.compile(r'-\s*\*\*([A-Za-z]+\s*§[\d\.]+)\*\*:\s*([^\n—\-]+)[—\-]\s*([^\n]+)')
            matches = pattern.findall(content)
            for clause_id, title, text in matches:
                clause_id = clause_id.strip()
                title = title.strip()
                text = text.strip()
                citation = f"{client_id.capitalize()} {clause_id}: {title}"
                self.clauses.append(PolicyClause(client_id, clause_id, title, text, citation))

        # Build IDF dictionary across all clauses
        total_docs = len(self.clauses)
        doc_freq: Dict[str, int] = {}
        for c in self.clauses:
            unique_tokens = set(c.tokens)
            for t in unique_tokens:
                doc_freq[t] = doc_freq.get(t, 0) + 1

        for t, freq in doc_freq.items():
            self.idf[t] = math.log((total_docs - freq + 0.5) / (freq + 0.5) + 1.0)

    def search_policy(self, client_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Hybrid search (Keyword BM25 + Vector Cosine) strictly filtered by client_id.
        Guarantees zero cross-tenant leakage.
        """
        target_client = client_id.lower()
        # Strictly filter by client_id
        candidate_clauses = [c for c in self.clauses if c.client_id == target_client]
        if not candidate_clauses:
            return []

        q_tokens = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9§\.\-]+\b', query)]
        if not q_tokens:
            return []

        results = []
        k1 = 1.5
        b = 0.75
        avg_dl = sum(len(c.tokens) for c in candidate_clauses) / max(len(candidate_clauses), 1)

        for clause in candidate_clauses:
            # 1. BM25 score
            bm25 = 0.0
            doc_len = len(clause.tokens)
            for t in q_tokens:
                if t in self.idf:
                    tf = clause.tokens.count(t)
                    idf_val = self.idf[t]
                    num = tf * (k1 + 1)
                    denom = tf + k1 * (1 - b + b * (doc_len / avg_dl))
                    bm25 += idf_val * (num / max(denom, 0.0001))

            # 2. Vector Cosine Similarity (TF-IDF vector space)
            # Create vector representation for query and document
            common_vocab = set(q_tokens).union(set(clause.tokens))
            dot_product = 0.0
            norm_q = 0.0
            norm_d = 0.0
            for term in common_vocab:
                idf_v = self.idf.get(term, 1.0)
                wq = (q_tokens.count(term)) * idf_v
                wd = (clause.tokens.count(term)) * idf_v
                dot_product += wq * wd
                norm_q += wq * wq
                norm_d += wd * wd

            cos_sim = 0.0
            if norm_q > 0 and norm_d > 0:
                cos_sim = dot_product / (math.sqrt(norm_q) * math.sqrt(norm_d))

            # Normalize BM25 to 0..1 scale approx
            norm_bm25 = min(bm25 / 15.0, 1.0)

            # Combined hybrid similarity score
            hybrid_score = round(0.45 * norm_bm25 + 0.55 * cos_sim, 4)

            results.append({
                "client_id": clause.client_id,
                "clause_id": clause.clause_id,
                "title": clause.title,
                "text": clause.text,
                "citation": clause.citation,
                "similarity_score": hybrid_score
            })

        # Sort descending by similarity score
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

# Global singleton
rag_engine = PolicyRAG()

def search_policy(client_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    return rag_engine.search_policy(client_id, query, top_k)
