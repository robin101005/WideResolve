"""Generates data/db.json (all simulated: no real client or patient data)."""
import json
clients = {
 "C1": {"name": "ShopEasy", "industry": "E-commerce", "tier": "Gold", "fee": 120000, "uptime": 99.9, "cap_pct": 10, "prefix": "SHOP"},
 "C2": {"name": "TelcoNet", "industry": "Telecom", "tier": "Platinum", "fee": 250000, "uptime": 99.95, "cap_pct": 15, "prefix": "TEL"},
 "C3": {"name": "MediCare Plus", "industry": "Healthcare", "tier": "Gold", "fee": 180000, "uptime": 99.9, "cap_pct": 10, "prefix": "MED"},
}
def clauses(c):
    p = c["prefix"]; allowed = round((1 - c["uptime"] / 100) * 43200, 1)
    return [
     {"id": f"{p}-4.1", "tags": ["outage"], "text": f"Monthly uptime must be at least {c['uptime']}% (about {allowed} minutes of downtime allowed in a 30-day month)."},
     {"id": f"{p}-4.2", "tags": ["outage"], "text": f"If uptime is missed, the client receives a service credit of 5% of the monthly fee for up to 60 minutes beyond the allowance and 10% above that, capped at {c['cap_pct']}% of the monthly fee."},
     {"id": f"{p}-4.3", "tags": ["outage"], "text": "Three or more outages within 90 days add 5% to the service credit (still subject to the cap)."},
     {"id": f"{p}-7.1", "tags": ["billing"], "text": "Duplicate or incorrect charges are credited in full within 5 business days."},
     {"id": f"{p}-7.2", "tags": ["billing"], "text": f"Invoices match the contracted monthly fee of INR {c['fee']:,} plus approved add-ons."},
     {"id": f"{p}-9.1", "tags": ["compliance"], "text": "Incidents involving legal claims or personal/patient data must be reviewed by the Compliance Lead before any resolution is offered."},
    ]
inv = lambda i, c, d, a: {"id": i, "client": c, "month": "2026-09", "description": d, "amount": a}
inc = lambda i, c, s, d, m, why: {"id": i, "client": c, "service": s, "date": d, "minutes": m, "cause": why}
db = {
 "clients": clients,
 "contracts": {k: clauses(v) for k, v in clients.items()},
 "invoices": [inv("INV-1101", "C1", "Monthly service fee", 120000),
              inv("INV-2041", "C2", "Monthly service fee", 250000), inv("INV-2042", "C2", "Support add-on", 4999), inv("INV-2043", "C2", "Support add-on", 4999),
              inv("INV-3101", "C3", "Monthly service fee", 180000)],
 "incidents": [inc("INC-501", "C1", "Checkout service", "2026-09-18", 95, "database failover error after a deployment"),
               inc("INC-601", "C2", "Network gateway", "2026-07-18", 45, "gateway memory leak"),
               inc("INC-602", "C2", "Network gateway", "2026-08-22", 60, "gateway certificate expiry"),
               inc("INC-603", "C2", "Network gateway", "2026-09-20", 120, "gateway failure after a firmware change"),
               inc("INC-701", "C3", "Patient portal", "2026-09-12", 180, "load balancer fault")],
 "past_tickets": [{"client": "C1", "id": "PT-11", "subject": "Invoice question", "date": "2026-06-03"},
                  {"client": "C2", "id": "PT-21", "subject": "Gateway outage credit", "date": "2026-07-20"},
                  {"client": "C2", "id": "PT-22", "subject": "Gateway outage again", "date": "2026-08-24"},
                  {"client": "C3", "id": "PT-31", "subject": "Portal login slow", "date": "2026-05-14"}],
 "samples": [
  {"client": "C2", "text": "Our invoice shows the support add-on charged twice for September. Please fix this now!", "expect": ["auto_resolve", None]},
  {"client": "C1", "text": "Our checkout was down on 18 Sept for over an hour. We want the SLA credits.", "expect": ["auto_resolve", None]},
  {"client": "C1", "text": "Our September invoice looks too high. Please refund the extra amount.", "expect": ["auto_resolve", None]},
  {"client": "C3", "text": "The patient portal was down on 12 Sept for hours and patient data may be exposed. We are considering legal action.", "expect": ["escalate", "Compliance Lead + Account Manager"]},
  {"client": "C2", "text": "Our network gateway is down again. This is the third outage this quarter and we want penalty credits.", "expect": ["escalate", "Account Manager"]},
  {"client": "C1", "text": "Our API was down on 25 Sept for a long time according to our monitoring. Please apply SLA credits.", "expect": ["escalate", "L2 Support Engineer"]},
 ],
}
json.dump(db, open("data/db.json", "w"), indent=1)
print("data/db.json written")
