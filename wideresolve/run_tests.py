"""Runs the 6 sample tickets and checks the decisions. Works with or without an API key."""
import agents as A
ok = 0
for i, s in enumerate(A.DB["samples"], 1):
    c = A.run_pipeline(s["client"], s["text"], save=False)
    got = [c["decision"]["action"], c["decision"]["route"]]
    good = got == s["expect"]; ok += good
    print(f"{'PASS' if good else 'FAIL'}  T{i} {c['client']:<14} expected={s['expect']} got={got}")
print(f"\n{ok}/{len(A.DB['samples'])} passed | AI mode: {'Claude' if A.llm_enabled() else 'offline rules'}")
raise SystemExit(0 if ok == len(A.DB["samples"]) else 1)
