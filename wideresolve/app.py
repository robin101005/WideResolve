import pandas as pd
import streamlit as st
import agents as A

st.set_page_config(page_title="WideResolve", layout="wide")
st.title("WideResolve")
st.caption("AI customer escalation resolution agent for Widesoftech")

portal = st.sidebar.radio("Portal", ["Client portal", "Admin portal"])
st.sidebar.subheader("Authority panel")
limit = st.sidebar.slider("Max auto-credit (INR)", 0, 100000, 25000, 1000)
thr = st.sidebar.slider("Min confidence to auto-resolve", 0.5, 1.0, 0.8, 0.05)
st.sidebar.caption("Change these and resubmit a ticket to see the decision flip.")
st.sidebar.caption("AI mode: " + ("Claude API" if A.llm_enabled() else "offline rules (no API key found)"))

def show_trail(case):
    for name, out in case["trail"]:
        st.markdown(f"**{name}**")
        st.json(out, expanded=False)

if portal == "Client portal":
    st.subheader("Client portal")
    cid = st.selectbox("Sign in as client company", list(A.DB["clients"]),
                       format_func=lambda k: f"{A.DB['clients'][k]['name']} ({A.DB['clients'][k]['industry']})")
    samples = [s["text"] for s in A.DB["samples"] if s["client"] == cid]
    pick = st.selectbox("Example tickets (or write your own below)", ["Write my own"] + samples)
    text = st.text_area("Describe your problem", value="" if pick == "Write my own" else pick, height=110)
    if st.button("Submit ticket", type="primary") and text.strip():
        with st.spinner("Investigating..."):
            case = A.run_pipeline(cid, text.strip(), limit, thr)
        (st.success if case["status"] == "Auto-resolved" else st.warning)(f"Status: {case['status']}")
        st.markdown("**Reply to the client**")
        st.write(case["reply"])
        with st.expander("Show how the AI decided"):
            show_trail(case)
else:
    st.subheader("Admin portal (Widesoftech)")
    cases = A.load_cases()
    auto = sum(c["status"] == "Auto-resolved" for c in cases)
    hrs = st.number_input("Assumed manual investigation hours per ticket (simulated estimate)", 0.5, 8.0, 2.0, 0.5)
    c1, c2, c3 = st.columns(3)
    c1.metric("Tickets", len(cases)); c2.metric("Auto-resolved", auto)
    c3.metric("Estimated engineer hours saved", f"{auto * hrs:.1f}")
    if not cases:
        st.info("No tickets yet. Submit one from the client portal.")
    else:
        st.dataframe(pd.DataFrame([{"id": c["id"], "client": c["client"], "status": c["status"], "route": c["route"], "ticket": c["text"][:70]} for c in cases]),
                     width="stretch", hide_index=True)
        cid = st.selectbox("Open a case", [c["id"] for c in reversed(cases)])
        case = next(c for c in cases if c["id"] == cid)
        st.write(f"**{case['client']}**: {case['text']}")
        st.write(f"**Status:** {case['status']}")
        if case["brief"]:
            st.markdown("**Handoff brief**")
            for line in case["brief"]:
                st.markdown(f"- {line}")
            note = st.text_input("Override note (optional)")
            b1, b2 = st.columns(2)
            if b1.button("Approve AI recommendation"):
                A.admin_action(case["id"], "approve"); st.rerun()
            if b2.button("Override"):
                A.admin_action(case["id"], "override", note or "no note"); st.rerun()
        with st.expander("Decision trail"):
            show_trail(case)
        with st.expander("Audit log"):
            p = A.DATA / "audit_log.jsonl"
            st.code(p.read_text() if p.exists() else "empty")
