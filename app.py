import streamlit as st
import boto3
import json
import uuid
import time
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. CREDENTIALS & CONFIGURATION
# ==========================================
# Securely fetching credentials from Streamlit Secrets
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]

BUCKET_NAME   = "auto-analyst-workspace-tanmay"
QUEUE_URL     = "https://sqs.us-east-1.amazonaws.com/240828341145/AnalystJobQueue"
REGION        = "us-east-1"

# ==========================================
# 2. INITIALIZE AWS CLIENTS
# ==========================================
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION
)
sqs_client = boto3.client(
    'sqs',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION
)

# ==========================================
# 3. PAGE CONFIG & GLOBAL STYLING
# ==========================================
st.set_page_config(page_title="Auto-Analyst", page_icon="⚡", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0a0c10; color: #e2e8f0; }
[data-testid="stSidebar"] { background-color: #0f1117; border-right: 1px solid #1e2433; }
.stApp::before {
    content:''; display:block; height:3px;
    background:linear-gradient(90deg,#6366f1,#8b5cf6,#a78bfa);
    position:fixed; top:0; left:0; right:0; z-index:9999;
}
.aa-header { padding:2.5rem 0 1.5rem; border-bottom:1px solid #1e2433; margin-bottom:2rem; }
.aa-eyebrow { font-family:'DM Mono',monospace; font-size:0.7rem; letter-spacing:0.15em; color:#6366f1; text-transform:uppercase; margin-bottom:0.5rem; }
.aa-title { font-size:2rem; font-weight:700; color:#f8fafc; margin:0; line-height:1.2; }
.aa-subtitle { font-size:0.9rem; color:#64748b; margin-top:0.4rem; }
.aa-section-label { font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.12em; color:#475569; text-transform:uppercase; margin-bottom:0.75rem; margin-top:0.25rem; }
.kpi-card { background:#0f1117; border:1px solid #1e2433; border-radius:12px; padding:1.25rem 1.5rem; position:relative; overflow:hidden; }
.kpi-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,#6366f1,#8b5cf6); }
.kpi-label { font-size:0.72rem; color:#64748b; text-transform:uppercase; letter-spacing:0.08em; font-weight:500; margin-bottom:0.5rem; }
.kpi-value { font-size:1.7rem; font-weight:700; color:#f1f5f9; line-height:1; font-variant-numeric:tabular-nums; }
.kpi-delta { font-size:0.75rem; color:#22c55e; margin-top:0.35rem; font-family:'DM Mono',monospace; }
.conclusion-card { background:linear-gradient(135deg,#0f1117 0%,#131929 100%); border:1px solid #1e2433; border-left:3px solid #6366f1; border-radius:0 12px 12px 0; padding:1.5rem 1.75rem; margin-bottom:2rem; color:#cbd5e1; font-size:0.95rem; line-height:1.7; }
.conclusion-label { font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.12em; color:#6366f1; text-transform:uppercase; margin-bottom:0.75rem; font-weight:500; }
.chart-card { background:#0f1117; border:1px solid #1e2433; border-radius:12px; padding:0.25rem; margin-bottom:1rem; }
.phase-row { display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem; }
.phase-dot { width:8px; height:8px; border-radius:50%; background:#1e2433; flex-shrink:0; }
.phase-dot.active { background:#6366f1; box-shadow:0 0 8px #6366f180; }
.phase-dot.done   { background:#22c55e; }
.phase-label { font-size:0.8rem; color:#64748b; }
.phase-label.active { color:#a5b4fc; font-weight:500; }
.phase-label.done   { color:#4ade80; }
.reanalyze-box { background:#0f1117; border:1px solid #1e2433; border-radius:12px; padding:1.25rem 1.5rem; margin-top:1rem; }
.reanalyze-tag { font-family:'DM Mono',monospace; font-size:0.65rem; color:#6366f1; text-transform:uppercase; letter-spacing:0.1em; }
.stTextArea textarea, .stTextInput input { background-color:#0a0c10 !important; border:1px solid #1e2433 !important; border-radius:8px !important; color:#e2e8f0 !important; font-family:'Inter',sans-serif !important; }
.stTextArea textarea:focus, .stTextInput input:focus { border-color:#6366f1 !important; box-shadow:0 0 0 2px #6366f130 !important; }
[data-testid="stFileUploader"] { background:#0a0c10; border:1px dashed #1e2433; border-radius:10px; }
[data-testid="stFileUploader"]:hover { border-color:#6366f1; }
div.stButton > button { background:linear-gradient(135deg,#6366f1,#8b5cf6) !important; color:#fff !important; font-weight:600 !important; border:none !important; border-radius:8px !important; padding:0.6rem 2rem !important; font-size:0.9rem !important; width:100% !important; }
div.stButton > button:hover { opacity:0.9 !important; }
[data-testid="stDownloadButton"] button { background:#0f1117 !important; color:#a5b4fc !important; border:1px solid #1e2433 !important; border-radius:8px !important; font-size:0.85rem !important; width:100% !important; }
[data-testid="stDownloadButton"] button:hover { border-color:#6366f1 !important; }
hr { border-color:#1e2433 !important; }
.dash-header { display:flex; align-items:baseline; gap:1rem; margin-bottom:1.5rem; padding-bottom:1rem; border-bottom:1px solid #1e2433; }
.dash-title  { font-size:1.25rem; font-weight:600; color:#f1f5f9; }
.dash-session { font-family:'DM Mono',monospace; font-size:0.7rem; color:#475569; padding:0.2rem 0.6rem; background:#131929; border-radius:4px; border:1px solid #1e2433; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. CHART ENGINE
# ==========================================
PLOTLY_THEME = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94a3b8", size=12),
    margin=dict(l=48, r=24, t=52, b=48),
    hoverlabel=dict(bgcolor="#1e2433", bordercolor="#334155",
                    font_color="#f1f5f9", font_family="Inter"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2433", font_color="#94a3b8"),
)
PALETTE = ["#6366f1","#8b5cf6","#06b6d4","#10b981","#f59e0b","#ef4444","#ec4899","#84cc16"]

def _axis_style(title, is_x=True):
    return dict(title_text=title, title_font=dict(size=11, color="#64748b"),
                tickfont=dict(size=10, color="#64748b"),
                gridcolor="#1e2433", showgrid=not is_x, zeroline=False,
                linecolor="#1e2433" if is_x else "rgba(0,0,0,0)")

def render_chart(chart: dict) -> go.Figure | None:
    c_type  = chart.get("type", "bar").lower()
    title   = chart.get("title", "")
    x_data  = chart.get("x_data", [])
    y_data  = chart.get("y_data", [])
    x_title = chart.get("x_title", "")
    y_title = chart.get("y_title", "")
    series  = chart.get("series", [])

    fig = go.Figure()
    is_radial = c_type in {"pie", "donut", "funnel"}

    if c_type == "bar":
        if series:
            for i, s in enumerate(series):
                fig.add_trace(go.Bar(name=s["name"], x=x_data, y=s["y_data"],
                                     marker_color=PALETTE[i % len(PALETTE)],
                                     hovertemplate=f"<b>%{{x}}</b><br>{s['name']}: %{{y:,.0f}}<extra></extra>"))
            fig.update_layout(barmode="group")
        else:
            fig.add_trace(go.Bar(x=x_data, y=y_data,
                                 marker_color=[PALETTE[i % len(PALETTE)] for i in range(len(x_data))],
                                 hovertemplate="<b>%{x}</b><br>%{y:,.2f}<extra></extra>"))

    elif c_type == "hbar":
        fig.add_trace(go.Bar(x=y_data, y=x_data, orientation='h',
                             marker=dict(color=y_data,
                                         colorscale=[[0,"#1e2433"],[1,"#6366f1"]],
                                         showscale=False),
                             hovertemplate="<b>%{y}</b>: %{x:,.2f}<extra></extra>"))
        fig.update_layout(yaxis=dict(autorange="reversed"))

    elif c_type == "line":
        if series:
            for i, s in enumerate(series):
                fig.add_trace(go.Scatter(name=s["name"], x=x_data, y=s["y_data"],
                                         mode='lines+markers',
                                         line=dict(color=PALETTE[i % len(PALETTE)], width=2.5),
                                         marker=dict(size=5)))
        else:
            fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines+markers',
                                     line=dict(color="#6366f1", width=2.5),
                                     marker=dict(size=5, color="#8b5cf6"),
                                     fill='tozeroy', fillcolor="rgba(99,102,241,0.08)"))

    elif c_type == "area":
        if series:
            for i, s in enumerate(series):
                fig.add_trace(go.Scatter(name=s["name"], x=x_data, y=s["y_data"],
                                         mode='lines', stackgroup='one',
                                         line=dict(color=PALETTE[i % len(PALETTE)], width=1.5)))
        else:
            fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines',
                                     fill='tozeroy', line=dict(color="#6366f1", width=2),
                                     fillcolor="rgba(99,102,241,0.12)"))

    elif c_type == "scatter":
        fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='markers',
                                 marker=dict(size=10, color="#6366f1", opacity=0.75,
                                             line=dict(color="#8b5cf6", width=1))))

    elif c_type == "pie":
        fig.add_trace(go.Pie(labels=x_data, values=y_data,
                             marker=dict(colors=PALETTE, line=dict(color="#0a0c10", width=2)),
                             textinfo='percent+label', textfont=dict(color="#e2e8f0", size=11)))

    elif c_type == "donut":
        fig.add_trace(go.Pie(labels=x_data, values=y_data, hole=0.55,
                             marker=dict(colors=PALETTE, line=dict(color="#0a0c10", width=2)),
                             textinfo='percent+label', textfont=dict(color="#e2e8f0", size=11)))

    elif c_type == "waterfall":
        measure = chart.get("measure", ["relative"] * len(x_data))
        fig.add_trace(go.Waterfall(x=x_data, y=y_data, measure=measure,
                                   connector=dict(line=dict(color="#1e2433")),
                                   increasing=dict(marker_color="#22c55e"),
                                   decreasing=dict(marker_color="#ef4444"),
                                   totals=dict(marker_color="#6366f1")))

    elif c_type == "funnel":
        fig.add_trace(go.Funnel(y=x_data, x=y_data,
                                marker=dict(color=PALETTE[:len(x_data)]),
                                textinfo="value+percent initial"))

    elif c_type == "heatmap":
        z_data   = chart.get("z_data", [])
        y_labels = chart.get("y_labels", [])
        if z_data and y_labels:
            fig.add_trace(go.Heatmap(z=z_data, x=x_data, y=y_labels,
                                     colorscale=[[0,"#0a0c10"],[0.5,"#312e81"],[1,"#6366f1"]]))
    else:
        fig.add_trace(go.Bar(x=x_data, y=y_data, marker_color="#6366f1"))

    layout = {**PLOTLY_THEME,
              "title": dict(text=title, font=dict(size=14, color="#f1f5f9", weight=600), x=0)}
    if not is_radial:
        layout["xaxis"] = _axis_style(x_title, is_x=True)
        layout["yaxis"] = _axis_style(y_title, is_x=False)
    fig.update_layout(**layout)
    return fig

# ==========================================
# 5. SESSION STATE INIT
# ==========================================
if "last_session" not in st.session_state:
    st.session_state.last_session = None

# ==========================================
# 6. DASHBOARD RENDERER
# ==========================================
def render_dashboard(insights_data: dict, session_id: str, filename: str):
    with st.container(key="dashboard_capture_target"):
        st.markdown(f"""
        <div class="dash-header">
            <span class="dash-title">📊 Executive Dashboard</span>
            <span class="dash-session">Session {session_id}</span>
            <span class="dash-session">{filename}</span>
        </div>""", unsafe_allow_html=True)

        # PART 1: THE CONCLUSION (Executive Summary)
        conclusion = insights_data.get("conclusion", "")
        if conclusion:
            st.markdown(f"""
            <div class="conclusion-card">
                <div class="conclusion-label">⬛ Executive Summary</div>
                {conclusion}
            </div>""", unsafe_allow_html=True)

        # PART 2: THE KPIs (Top-line Metrics)
        kpis = insights_data.get("kpis", [])
        if kpis:
            st.markdown('<div class="aa-section-label">Key Performance Indicators</div>', unsafe_allow_html=True)
            cols = st.columns(min(len(kpis), 4))
            for idx, kpi in enumerate(kpis):
                delta_html = f'<div class="kpi-delta">{kpi.get("delta","")}</div>' if kpi.get("delta") else ""
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">{kpi.get("label","Metric")}</div>
                        <div class="kpi-value">{kpi.get("value","—")}</div>
                        {delta_html}
                    </div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # PART 3: THE CHARTS (Visual Evidence)
        charts = insights_data.get("charts", [])
        if charts:
            st.markdown('<div class="aa-section-label">Visual Analysis</div>', unsafe_allow_html=True)
            FULL_WIDTH = {"line", "area", "waterfall", "heatmap"}
            i = 0
            while i < len(charts):
                chart  = charts[i]
                c_type = chart.get("type", "bar").lower()
                reasoning = chart.get("reasoning", "")

                if c_type in FULL_WIDTH:
                    fig = render_chart(chart)
                    if fig:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                        if reasoning:
                            st.caption(f"💡 **AI Reasoning:** {reasoning}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    i += 1
                else:
                    left, right = st.columns(2, gap="medium")
                    for col_c in [left, right]:
                        if i >= len(charts):
                            break
                        c = charts[i]
                        fig = render_chart(c)
                        if fig:
                            with col_c:
                                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                                if c.get("reasoning"):
                                    st.caption(f"💡 **AI Reasoning:** {c['reasoning']}")
                                st.markdown('</div>', unsafe_allow_html=True)
                        i += 1

    # PART 4: THE EXPORT STRIP
    st.markdown("---")
    st.markdown('<div class="aa-section-label">Export</div>', unsafe_allow_html=True)

    report_md  = f"# Autonomous Analysis Report\n**Session:** {session_id} | **File:** {filename}\n\n"
    report_md += f"### Executive Summary\n{insights_data.get('conclusion','')}\n\n"
    if kpis:
        report_md += "### Key Performance Indicators\n"
        for kpi in kpis:
            report_md += f"- **{kpi.get('label')}:** {kpi.get('value')}\n"

    dl1, dl2, dl3 = st.columns(3, gap="small")
    with dl1:
        st.download_button("📄 Executive Report (.md)", data=report_md, file_name=f"Report_{session_id}.md", mime="text/markdown")
    with dl2:
        st.download_button("💾 Raw Insights (.json)", data=json.dumps(insights_data, indent=2), file_name=f"Insights_{session_id}.json", mime="application/json")
    with dl3:
        st.download_button("📊 Chart Data (.json)", data=json.dumps(insights_data.get("charts",[]), indent=2), file_name=f"Charts_{session_id}.json", mime="application/json")

    # PART 5: EXACT SNAPSHOT
    st.components.v1.html("""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <button id="snap-btn" style="
        background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;font-weight:600;
        border:none;border-radius:8px;padding:0.6rem 2rem;font-size:0.9rem;
        width:100%;cursor:pointer;">
        🖼️ Download Exact Dashboard Snapshot
    </button>
    <script>
    document.getElementById('snap-btn').onclick = function () {
        const doc = window.parent.document;
        const target = doc.querySelector('.st-key-dashboard_capture_target');
        if (!target) { alert('Could not find the dashboard container.'); return; }
        html2canvas(target, { backgroundColor: '#0a0c10', scale: 2, useCORS: true })
            .then(canvas => {
                const link = doc.createElement('a');
                link.download = 'Dashboard_Snapshot.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            })
            .catch(err => alert('Snapshot failed: ' + err));
    };
    </script>
    """, height=70)

    st.success("✓ Pipeline completed.")

# ==========================================
# 7. POLLING HELPER
# ==========================================
def poll_for_insights(insights_key: str, phases: list[str], only_analyze: bool = False) -> dict | None:
    phase_placeholder = st.empty()
    progress_bar      = st.progress(0)

    def draw_phases(active_idx):
        html = ""
        for pi, ph in enumerate(phases):
            if pi < active_idx:     dot_cls, lbl_cls = "done","done"
            elif pi == active_idx:  dot_cls, lbl_cls = "active","active"
            else:                   dot_cls, lbl_cls = "",""
            html += (f'<div class="phase-row">'
                     f'<div class="phase-dot {dot_cls}"></div>'
                     f'<span class="phase-label {lbl_cls}">{ph}</span>'
                     f'</div>')
        phase_placeholder.markdown(html, unsafe_allow_html=True)

    draw_phases(0)
    
    max_polls    = 36 if only_analyze else 72      
    phase_breaks = [4] if only_analyze else [8, 24] 

    for i in range(max_polls):
        try:
            resp = s3_client.get_object(Bucket=BUCKET_NAME, Key=insights_key)
            data = json.loads(resp['Body'].read().decode('utf-8'))
            draw_phases(len(phases))
            progress_bar.progress(100)
            phase_placeholder.empty()
            progress_bar.empty()
            return data
        except s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchKey':
                st.error(f"S3 error: {e}")
                return None
            
            pct = min(10 + i * (90 // max_polls), 92)
            
            if only_analyze:
                active = 0 if i < phase_breaks[0] else 1
            else:
                active = 0 if i < phase_breaks[0] else (1 if i < phase_breaks[1] else 2)
                
            draw_phases(active)
            progress_bar.progress(pct)
            time.sleep(2)

    phase_placeholder.empty()
    progress_bar.empty()
    return None

# ==========================================
# 8. APP LAYOUT
# ==========================================
st.markdown("""
<div class="aa-header">
    <div class="aa-eyebrow">Autonomous Data Analysis System</div>
    <div class="aa-title">Turn your data into decisions.</div>
    <div class="aa-subtitle">Upload a dataset, define your goals — the AI pipeline handles the rest.</div>
</div>
""", unsafe_allow_html=True)

left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    st.markdown('<div class="aa-section-label">Dataset</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Drop your CSV here", type=['csv'],
                                     label_visibility="collapsed")
    if uploaded_file:
        st.caption(f"✓ {uploaded_file.name}  ·  {uploaded_file.size / 1024:.1f} KB")

with right_col:
    st.markdown('<div class="aa-section-label">Context & Goals</div>', unsafe_allow_html=True)
    data_description = st.text_area("What is this data about?",
                                    placeholder="e.g. Weekly retail sales across 10 store locations, Jan–Dec 2024.",
                                    height=90, label_visibility="collapsed")
    stakeholder_needs = st.text_area("What business questions need answering?",
                                     placeholder="e.g. Which stores are underperforming? Show monthly revenue trends.",
                                     height=110, label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# ---- Re-analyze panel ----
reanalyze_clicked = False
new_question      = ""

if st.session_state.last_session:
    last = st.session_state.last_session
    st.markdown(f"""
    <div class="reanalyze-box">
        <div class="reanalyze-tag">⚡ Re-analyze — data already cleaned</div>
        <p style="color:#94a3b8;font-size:0.85rem;margin:0.6rem 0 0.9rem;">
            Session <code style="color:#a5b4fc">{last['session_id']}</code> ·
            <strong style="color:#e2e8f0">{last['filename']}</strong> is still in the pipeline.
            Ask a different question without re-uploading or re-cleaning.
        </p>
    </div>
    """, unsafe_allow_html=True)
    new_question = st.text_area(
        "New business question for the same dataset",
        placeholder="e.g. Now show me the bottom 3 stores and their monthly trend.",
        height=80, key="reanalyze_q"
    )
    ra_col, _ = st.columns([1, 3])
    with ra_col:
        reanalyze_clicked = st.button("🔁 Re-analyze (skip prepare & clean)")

run_col, _ = st.columns([1, 3])
with run_col:
    run_clicked = st.button("⚡ Run Full Pipeline")

st.markdown("---")

# ==========================================
# 9. RE-ANALYZE FLOW
# ==========================================
if reanalyze_clicked:
    last = st.session_state.last_session
    if not new_question.strip():
        st.error("Please enter a new business question.")
    else:
        version_tag   = str(uuid.uuid4())[:6]
        cleaned_s3_url = f"s3://{BUCKET_NAME}/{last['cleaned_key']}"
        base_key       = last['cleaned_key'].replace("cleaned/", "reports/").replace(".parquet", "")
        insights_key   = f"{base_key}_{version_tag}_insights.json"

        payload = {
            "session_id":   last["session_id"],
            "phase":        "analyze",
            "file_url":     cleaned_s3_url,
            "needs":        new_question,
            "insights_key": f"{BUCKET_NAME}/{insights_key}",
        }
        sqs_client.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(payload))
        st.info(f"Re-analyze dispatched · will write to `{insights_key}`")

        phases = ["Analyze · Insight extraction & chart planning", "Done"]
        insights_data = poll_for_insights(insights_key, phases, only_analyze=True)

        if insights_data:
            st.session_state.last_session["insights_data"] = insights_data
            render_dashboard(insights_data, last["session_id"], last["filename"])
        else:
            st.error("Re-analyze timed out (3 minutes). Check Lambda CloudWatch logs for errors.")

# ==========================================
# 10. FULL PIPELINE FLOW
# ==========================================
if run_clicked:
    if uploaded_file is None:
        st.error("Please upload a CSV dataset first.")
    elif not stakeholder_needs.strip():
        st.error("Please describe what business questions you want answered.")
    else:
        with st.spinner("Uploading dataset to S3…"):
            try:
                session_id = str(uuid.uuid4())[:8]
                file_key   = f"raw/{session_id}_{uploaded_file.name}"
                s3_client.upload_fileobj(uploaded_file, BUCKET_NAME, file_key)

                payload = {
                    "session_id": session_id,
                    "phase":      "prepare",
                    "file_url":   f"s3://{BUCKET_NAME}/{file_key}",
                    "description": data_description,
                    "needs":       stakeholder_needs,
                }
                sqs_client.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(payload))
                st.info(f"Full pipeline triggered · Session `{session_id}`")
            except Exception as e:
                st.error(f"Failed to start pipeline: {e}")
                st.stop()

        phases = [
            "Prepare · Schema extraction & Parquet conversion",
            "Process · AI-powered data cleaning",
            "Analyze · Insight extraction & chart planning",
        ]
        insights_key = file_key.replace("raw/", "reports/").replace(".csv", "_insights.json")
        insights_data = poll_for_insights(insights_key, phases, only_analyze=False)

        if insights_data:
            processed_key = file_key.replace("raw/", "processed/").replace(".csv", ".parquet")
            cleaned_key   = processed_key.replace("processed/", "cleaned/")

            st.session_state.last_session = {
                "session_id":   session_id,
                "filename":     uploaded_file.name,
                "cleaned_key":  cleaned_key,
                "insights_data": insights_data,
            }
            render_dashboard(insights_data, session_id, uploaded_file.name)
        else:
            st.error("Pipeline timed out (6 minutes). Check the Lambda CloudWatch logs for crash traces.")