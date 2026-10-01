"""
Policy Agent for OmniResolve.
Retrieves tenant-isolated policy clauses matching customer complaints and extracted intent.
"""

from typing import List, Dict, Any
from engine.rag import search_policy
from engine.types import CaseFile

class PolicyAgent:
    def evaluate_policies(self, case_file: CaseFile) -> List[Dict[str, Any]]:
        client_id = case_file.client_id
        # Use sanitized complaint + intent issue type as query
        issue_type = case_file.intent.get("issue_type", "")
        query = f"{issue_type} {case_file.sanitized_complaint}"

        matches = search_policy(client_id, query, top_k=3)
        case_file.relevant_policies = matches
        return matches

policy_agent = PolicyAgent()
