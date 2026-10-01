"""Deterministic policy layer: the AI proposes, this code decides what is allowed."""
ROUTES = {"compliance": "Compliance Lead + Account Manager", "over_limit": "Account Manager",
          "conflict": "L2 Support Engineer", "low_confidence": "L2 Support Engineer", "no_clause": "L2 Support Engineer"}
PRIORITY = ["compliance", "over_limit", "conflict", "low_confidence", "no_clause"]
RIGHTS = {"CLIENT": {"submit", "view"}, "ADMIN": {"submit", "view", "approve", "override"}}

def authorize(role, action):
    if action not in RIGHTS.get(role, set()):
        raise PermissionError(f"Role {role} may not {action}")

def gate(res, flags, limit, thr):
    why = {}
    if flags.get("legal") or flags.get("sensitive"):
        why["compliance"] = "Legal threat or personal/patient data involved: compliance issues are never auto-resolved"
    if res["amount"] > limit:
        why["over_limit"] = f"Amount INR {res['amount']:,.0f} is above the auto-resolve limit of INR {limit:,.0f}"
    if res.get("conflict"):
        why["conflict"] = res["conflict"]
    if res["confidence"] < thr:
        why["low_confidence"] = f"Confidence {res['confidence']:.0%} is below the {thr:.0%} threshold"
    if not res["clauses"]:
        why["no_clause"] = "No contract clause found for this issue"
    if why:
        key = next(k for k in PRIORITY if k in why)
        return {"action": "escalate", "route": ROUTES[key], "reasons": list(why.values())}
    return {"action": "auto_resolve", "route": None,
            "reasons": ["Amount within limit, contract clause is clear, evidence is consistent, confidence is high"]}
