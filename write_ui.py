code = '''import streamlit as st
import requests

BACKEND = "http://localhost:8000"

st.set_page_config(page_title="VeriMind AI", page_icon="V", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#080c10!important;color:#c8d6e5!important;font-family:'DM Mono',monospace!important;}
[data-testid="stSidebar"]{background:#0b1017!important;border-right:1px solid #1a2535!important;}
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important;}
.vm-header{display:flex;align-items:center;gap:14px;padding:28px 0 20px 0;border-bottom:1px solid #1a2535;margin-bottom:24px;}
.vm-logo{width:42px;height:42px;background:linear-gradient(135deg,#0d7eff 0%,#00d4aa 100%);clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);animation:pulse-logo 3s ease-in-out infinite;}
@keyframes pulse-logo{0%,100%{opacity:1}50%{opacity:0.7}}
.vm-title{font-family:'Syne',sans-serif!important;font-size:26px!important;font-weight:800!important;background:linear-gradient(90deg,#0d7eff,#00d4aa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.vm-subtitle{font-size:11px;color:#3d5a7a;letter-spacing:2px;text-transform:uppercase;margin-top:3px;}
.vm-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:24px;}
.vm-stat{background:#0e1620;border:1px solid #1a2535;border-radius:8px;padding:14px 16px;position:relative;overflow:hidden;}
.vm-stat::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#0d7eff,#00d4aa);}
.vm-stat-label{font-size:10px;color:#3d5a7a;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;}
.vm-stat-value{font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#e8f4ff;}
.vm-stat-sub{font-size:10px;color:#3d5a7a;margin-top:2px;}
.vm-pipeline{display:flex;align-items:center;gap:6px;margin-bottom:20px;padding:12px 16px;background:#0e1620;border:1px solid #1a2535;border-radius:8px;font-size:11px;color:#3d5a7a;}
.vm-agent-pill{padding:4px 10px;border-radius:4px;font-size:10px;font-weight:500;}
.vm-agent-researcher{background:#0d2a4a;color:#0d7eff;border:1px solid #0d4a8a;}
.vm-agent-critic{background:#2a1a0d;color:#ff8c0d;border:1px solid #8a4a0d;}
.vm-agent-summarizer{background:#0d2a1f;color:#00d4aa;border:1px solid #0d6a4a;}
.vm-agent-insight{background:#2a0d2a;color:#d400d4;border:1px solid #6a0d6a;}
.vm-message{padding:16px 20px;border-radius:8px;margin-bottom:12px;font-size:13px;line-height:1.7;}
.vm-message-user{background:#0e1e30;border:1px solid #1a3550;border-left:3px solid #0d7eff;color:#a8c4e0;}
.vm-message-ai{background:#0a1a14;border:1px solid #1a3530;border-left:3px solid #00d4aa;color:#c8e0d6;}
.vm-message-header{font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;}
.vm-message-header-user{color:#0d7eff;}
.vm-message-header-ai{color:#00d4aa;}
.conf-high{background:#0d2a1f;color:#00d4aa;border:1px solid #00d4aa44;display:inline-block;padding:4px 12px;border-radius:4px;font-size:11px;margin-bottom:10px;}
.conf-medium{background:#2a200d;color:#ffa500;border:1px solid #ffa50044;display:inline-block;padding:4px 12px;border-radius:4px;font-size:11px;margin-bottom:10px;}
.conf-low{background:#2a0d0d;color:#ff4444;border:1px solid #ff444444;display:inline-block;padding:4px 12px;border-radius:4px;font-size:11px;margin-bottom:10px;}
.vm-thinking{display:flex;align-items:center;gap:10px;padding:14px 20px;background:#0e1620;border:1px solid #1a2535;border-radius:8px;font-size:12px;color:#3d5a7a;}
.vm-dots span{display:inline-block;width:6px;height:6px;background:#0d7eff;border-radius:50%;margin:0 2px;animation:bounce 1.2s infinite;}
.vm-dots span:nth-child(2){animation-delay:0.2s;background:#0090cc;}
.vm-dots span:nth-child(3){animation-delay:0.4s;background:#00d4aa;}
@keyframes bounce{0%,80%,100%{transform:translateY(0);opacity:0.4}40%{transform:translateY(-6px);opacity:1}}
.stButton>button{background:#0e1620!important;border:1px solid #1a3550!important;color:#0d7eff!important;border-radius:6px!important;font-size:11px!important;letter-spacing:1px!important;text-transform:uppercase!important;}
</style>""", unsafe_allow_html=True)

for k,v in {"messages":[],"plan":"free","collection":"default","domain":"general","total_queries":0,"conf_scores":[],"active_task":"ask"}.items():
    if k not in st.session_state: st.session_state[k]=v

with st.sidebar:
    st.markdown('<div style="padding:20px 0 10px 0;"><div style="font-family:Syne,sans-serif;font-size:18px;font-weight:800;background:linear-gradient(90deg,#0d7eff,#00d4aa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">VeriMind AI</div><div style="font-size:10px;color:#3d5a7a;letter-spacing:2px;">ENTERPRISE INTELLIGENCE PLATFORM</div></div>', unsafe_allow_html=True)
    plan=st.radio("Plan",["free","premium"],index=0 if st.session_state.plan=="free" else 1,format_func=lambda x:"FREE TIER" if x=="free" else "PREMIUM",label_visibility="collapsed")
    st.session_state.plan=plan
    domain=st.selectbox("Domain",["general","finance","legal","hr"],format_func=lambda x:{"general":"General","finance":"Finance","legal":"Legal","hr":"HR"}[x],label_visibility="collapsed")
    st.session_state.domain=domain
    uploaded=st.file_uploader("Upload PDF",type=["pdf"],label_visibility="collapsed")
    if uploaded:
        col_name=uploaded.name.replace(".pdf","").replace(" ","_").lower()
        if st.button("INGEST DOCUMENT",use_container_width=True):
            with st.spinner("Processing..."):
                try:
                    resp=requests.post(f"{BACKEND}/ingest?collection={col_name}",files={"file":(uploaded.name,uploaded.getvalue(),"application/pdf")},timeout=300)
                    resp.raise_for_status(); data=resp.json()
                    st.session_state.collection=col_name
                    st.success(f"Done! {data['pages']} pages ingested")
                except Exception as e: st.error(f"Error: {e}")
    if st.session_state.collection!="default":
        if st.button("RESET TO TESLA 10-K",use_container_width=True):
            st.session_state.collection="default"; st.rerun()
    if st.button("LOAD HISTORY",use_container_width=True):
        try:
            hist=requests.get(f"{BACKEND}/history?limit=10",timeout=10).json()
            st.session_state["history_data"]=hist
        except: st.warning("Could not reach backend.")
    if "history_data" in st.session_state:
        for item in st.session_state["history_data"]:
            c=item["confidence"]
            with st.expander(f"{item['query'][:35]}"):
                st.markdown(f'{item["draft"][:300]}')

st.markdown('<div class="vm-header"><div class="vm-logo"></div><div><div class="vm-title">VeriMind AI</div><div class="vm-subtitle">Multi-Agent Document Intelligence Platform</div></div></div>',unsafe_allow_html=True)
scores=st.session_state.conf_scores; avg_c=round(sum(scores)/len(scores)) if scores else 0
doc_lbl=st.session_state.collection.replace("_"," ").upper() if st.session_state.collection!="default" else "TESLA 10-K"
st.markdown(f\'<div class="vm-stats"><div class="vm-stat"><div class="vm-stat-label">Queries Run</div><div class="vm-stat-value">{st.session_state.total_queries}</div><div class="vm-stat-sub">this session</div></div><div class="vm-stat"><div class="vm-stat-label">Avg Confidence</div><div class="vm-stat-value">{"X" if not scores else str(avg_c)+"%"}</div><div class="vm-stat-sub">critic verified</div></div><div class="vm-stat"><div class="vm-stat-label">Active Document</div><div class="vm-stat-value" style="font-size:13px;">{doc_lbl}</div><div class="vm-stat-sub">{st.session_state.domain.upper()} MODE</div></div></div>\',unsafe_allow_html=True)
st.markdown(\'<div class="vm-pipeline"><span>AGENT PIPELINE</span><span style="margin-left:10px"></span><span class="vm-agent-pill vm-agent-researcher">Researcher</span><span style="color:#1a2535;margin:0 4px">-></span><span class="vm-agent-pill vm-agent-critic">Critic</span><span style="color:#1a2535;margin:0 4px">-></span><span class="vm-agent-pill vm-agent-summarizer">Summarizer</span><span style="color:#1a2535;margin:0 4px">-></span><span class="vm-agent-pill vm-agent-insight">Insight</span><span style="margin-left:auto;font-size:10px;">LANGGRAPH ORCHESTRATED</span></div>\',unsafe_allow_html=True)

task_cols=st.columns(4)
tasks=[("ask","Q","Ask Question"),("summarize","S","Summarize"),("insights","I","Insights"),("validate","V","Validate")]
for i,(task_val,icon,label) in enumerate(tasks):
    with task_cols[i]:
        is_active=st.session_state.active_task==task_val
        b="#0d7eff" if is_active else "#1a2535"; bg="#0d2a4a" if is_active else "#0e1620"; c="#0d7eff" if is_active else "#3d5a7a"
        st.markdown(f\'<div style="padding:12px;background:{bg};border:1px solid {b};border-radius:6px;text-align:center;margin-bottom:4px;"><div style="font-size:20px;margin-bottom:4px;">{icon}</div><div style="font-size:10px;color:{c};letter-spacing:1px;text-transform:uppercase;">{label}</div></div>\',unsafe_allow_html=True)
        if st.button(label,key=f"task_{task_val}",use_container_width=True): st.session_state.active_task=task_val; st.rerun()

for msg in st.session_state.messages:
    if msg["role"]=="user":
        st.markdown(f\'<div class="vm-message vm-message-user"><div class="vm-message-header vm-message-header-user">USER QUERY</div>{msg["content"]}</div>\',unsafe_allow_html=True)
    else:
        conf=msg.get("confidence",0); cc="conf-high" if conf>=80 else "conf-medium" if conf>=60 else "conf-low"
        cl="HIGH CONFIDENCE" if conf>=80 else "MEDIUM CONFIDENCE" if conf>=60 else "LOW CONFIDENCE"
        ch=f\'<div class="{cc}">{cl} {conf}%</div>\' if conf>0 else ""
        tu=msg.get("task","ask")
        content=msg.get("insights","") if tu=="insights" and msg.get("insights") else msg.get("summary","") if tu=="summarize" and msg.get("summary") else msg.get("content","")
        st.markdown(f\'<div class="vm-message vm-message-ai"><div class="vm-message-header vm-message-header-ai">VERIMIND RESPONSE</div>{ch}{content}</div>\',unsafe_allow_html=True)
        if msg.get("context"):
            with st.expander("SOURCE CONTEXT"): st.markdown(f\'<div style="font-size:12px;color:#8aabb0;line-height:1.8;">{msg["context"]}</div>\',unsafe_allow_html=True)
        if msg.get("explanation"):
            with st.expander("WHY THIS ANSWER?"): st.markdown(f\'<div style="font-size:12px;color:#8aabb0;line-height:1.8;">{msg["explanation"]}</div>\',unsafe_allow_html=True)

active_task=st.session_state.active_task
placeholders={"ask":"Query the document intelligence layer...","summarize":"Specify section to summarize...","insights":"What should VeriMind analyze?","validate":"Paste a claim to fact-check..."}
st.markdown(f\'<div style="font-size:10px;color:#3d5a7a;letter-spacing:2px;margin-bottom:8px;">ACTIVE MODE: {active_task.upper()}</div>\',unsafe_allow_html=True)

if user_input:=st.chat_input(placeholders.get(active_task,"Query VeriMind AI...")):
    st.session_state.messages.append({"role":"user","content":user_input})
    st.markdown(f\'<div class="vm-message vm-message-user"><div class="vm-message-header vm-message-header-user">USER QUERY</div>{user_input}</div>\',unsafe_allow_html=True)
    thinking=st.empty()
    thinking.markdown(\'<div class="vm-thinking"><div class="vm-dots"><span></span><span></span><span></span></div><span>Agent council deliberating...</span></div>\',unsafe_allow_html=True)
    try:
        resp=requests.post(f"{BACKEND}/orchestrate",json={"query":user_input,"task":active_task,"domain":st.session_state.domain,"plan":st.session_state.plan,"collection":st.session_state.collection},timeout=120)
        resp.raise_for_status(); data=resp.json()
        draft=data.get("draft","No response."); context=data.get("context",""); summary=data.get("summary","")
        insights=data.get("insights",""); explanation=data.get("explanation",""); confidence=data.get("confidence",0)
    except Exception as e: draft,context,summary,insights,explanation,confidence=f"Error: {e}","","","","",0
    thinking.empty()
    st.session_state.total_queries+=1
    if confidence>0: st.session_state.conf_scores.append(confidence)
    cc="conf-high" if confidence>=80 else "conf-medium" if confidence>=60 else "conf-low"
    cl="HIGH CONFIDENCE" if confidence>=80 else "MEDIUM CONFIDENCE" if confidence>=60 else "LOW CONFIDENCE"
    ch=f\'<div class="{cc}">{cl} {confidence}%</div>\' if confidence>0 else ""
    display=insights if active_task=="insights" and insights else summary if active_task=="summarize" and summary else draft
    st.markdown(f\'<div class="vm-message vm-message-ai"><div class="vm-message-header vm-message-header-ai">VERIMIND RESPONSE</div>{ch}{display}</div>\',unsafe_allow_html=True)
    if context:
        with st.expander("SOURCE CONTEXT"): st.markdown(f\'<div style="font-size:12px;color:#8aabb0;line-height:1.8;">{context}</div>\',unsafe_allow_html=True)
    if explanation:
        with st.expander("WHY THIS ANSWER?"): st.markdown(f\'<div style="font-size:12px;color:#8aabb0;line-height:1.8;">{explanation}</div>\',unsafe_allow_html=True)
    st.session_state.messages.append({"role":"assistant","content":draft,"task":active_task,"context":context,"summary":summary,"insights":insights,"explanation":explanation,"confidence":confidence})
    st.rerun()
'''

with open("ui.py", "w", encoding="utf-8") as f:
    f.write(code)
print("Done! ui.py created successfully!")