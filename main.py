import streamlit as st
import sqlite3
import os
import base64
import smtplib
from datetime import datetime
from collections import Counter
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Load .env ──────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Optional imports (graceful fallback) ──────────────────
try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator
    TRANSLATE_AVAILABLE = True
except ImportError:
    TRANSLATE_AVAILABLE = False

# ════════════════════════════════════════════════════════════
# CONFIG — 100% FREE SERVICES
# ════════════════════════════════════════════════════════════
#  Service             Free Tier          Where to get
#  ──────────────────────────────────────────────────────────
#  Groq API          → Free forever       console.groq.com
#  Brevo SMTP        → 300 emails/day     brevo.com (no card)
#  gTTS              → Free forever       pip install gtts
#  deep-translator   → Free forever       pip install deep-translator
#  SQLite            → Free forever       built into Python
# ════════════════════════════════════════════════════════════

GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "")
BREVO_SMTP_LOGIN = os.getenv("BREVO_SMTP_LOGIN", "")
BREVO_SMTP_KEY   = os.getenv("BREVO_SMTP_KEY", "")
EMAIL_FROM       = os.getenv("EMAIL_FROM", "")
DB_FILE          = os.getenv("DB_FILE", "farmer_twin.db")

# ════════════════════════════════════════════════════════════
# DATA
# ════════════════════════════════════════════════════════════
LANGUAGES = {
    "English": "en", "Hindi": "hi", "Kannada": "kn", "Tamil": "ta",
    "Telugu": "te", "Marathi": "mr", "Bengali": "bn", "Gujarati": "gu",
    "Punjabi": "pa", "Malayalam": "ml", "Odia": "or", "Assamese": "as",
}

BIAS_INFO = {
    "Loss Aversion":   {"emoji": "🛡️", "color": "#C0392B", "desc": "Fear of loss stops you from switching crops/strategies even when data says otherwise.", "nudge_hint": "remind that staying still is also a risk"},
    "Present Bias":    {"emoji": "⏰", "color": "#E67E22", "desc": "You always pick quick money over long-term profit.", "nudge_hint": "show concrete future rupees vs today's gain"},
    "Anchoring":       {"emoji": "⚓", "color": "#8E44AD", "desc": "Stuck on a past price or old decision — judge everything relative to it.", "nudge_hint": "present fresh data without comparing to old anchor"},
    "Social Proof":    {"emoji": "👥", "color": "#2980B9", "desc": "You copy neighbours without checking if it fits your land.", "nudge_hint": "highlight successful farmers who did differently"},
    "Overconfidence":  {"emoji": "💪", "color": "#27AE60", "desc": "Trust gut over warnings — feels like experience, is actually risk.", "nudge_hint": "use stories of similar confident farmers who lost"},
    "Status Quo Bias": {"emoji": "🔒", "color": "#7F8C8D", "desc": "Refuse new techniques even when proven — change feels dangerous.", "nudge_hint": "frame as small reversible experiment, not permanent change"},
}

FALLBACK_NUDGES = {
    "Loss Aversion":   "Bhai, kuch nahi karna bhi ek risk hai. Agar aap puraani raah pe chalte raho, toh bhi loss ho sakta hai. Ek chhota kadam uthao — poora khet nahi, sirf ek khet mein try karo.",
    "Present Bias":    "Aaj ka Rs.1000 acha lagta hai, lekin 6 mahine mein Rs.3000 aur bhi acha lagega. Apne bacchon ke liye socho — future ka fayda asli fayda hai.",
    "Anchoring":       "Pichhle saal ki rate alag thi. Aaj ka market alag hai. Purani baat ko chod do, aaj ka data dekho — wahi sach hai.",
    "Social Proof":    "Aapka padosi aapki zameen nahi jaanta. Aapki mitti, paani, knowledge alag hai. Apne liye socho.",
    "Overconfidence":  "20 saal ka anubhav bahut keemat hai — lekin weather aur market rooz badle hain. Ek baar data bhi dekh lo, phir decide karo.",
    "Status Quo Bias": "Naya try karna matlab sab kuch badalna nahi. Sirf ek chhoti jagah pe try karo. Kaam aaya — badha lo. Nahi — kuch nahi gaya.",
}

DECISIONS = [
    {"id": "d1", "question": "Mandi price dropped 20%. What do you do?", "options": [
        ("Hold stock and wait for price to rise", "Loss Aversion"),
        ("Sell now to recover at least some money", "Present Bias"),
        ("Check last year's price and decide", "Anchoring"),
        ("Do what other farmers in village did", "Social Proof")]},
    {"id": "d2", "question": "Government scheme offers subsidy for drip irrigation. Your response?", "options": [
        ("I'll stick to flood irrigation — it always worked", "Status Quo Bias"),
        ("I'll apply only if my neighbour does first", "Social Proof"),
        ("I'll take it — free money now is better", "Present Bias"),
        ("Drip irrigation will fail on MY land, I know it", "Overconfidence")]},
    {"id": "d3", "question": "Expert recommends switching from wheat to millets this season. You?", "options": [
        ("No way — what if millets fail? Wheat is safe", "Loss Aversion"),
        ("What is my neighbour planting? I'll plant same", "Social Proof"),
        ("Millets take too long — wheat money comes faster", "Present Bias"),
        ("I've farmed 20 years. I know better than experts", "Overconfidence")]},
    {"id": "d4", "question": "Weather forecast says heavy rain in 3 days. You plan to harvest tomorrow. What do you do?", "options": [
        ("Harvest tomorrow as planned — forecast is often wrong", "Overconfidence"),
        ("Wait and see what others in village do first", "Social Proof"),
        ("Harvest now even if crop not fully ready — avoid risk", "Loss Aversion"),
        ("Last time forecast was wrong, so I'll ignore it", "Anchoring")]},
    {"id": "d5", "question": "A new app gives real-time mandi prices. Do you use it?", "options": [
        ("No — I trust my own experience and contacts", "Overconfidence"),
        ("No — too new, too risky, might be wrong", "Status Quo Bias"),
        ("Only if everyone else in my village starts using it", "Social Proof"),
        ("Apps always show old rates. Last time it was wrong", "Anchoring")]},
    {"id": "d6", "question": "Bank offers low-interest crop loan with 1-year repayment. You?", "options": [
        ("Avoid — debt is always dangerous no matter what", "Loss Aversion"),
        ("Take it only if my neighbour also takes it", "Social Proof"),
        ("Take it — use it for immediate needs, repay later", "Present Bias"),
        ("Banks always cause problems. I've seen it happen", "Anchoring")]},
    {"id": "d7", "question": "Organic farming could increase profit by 30% in 2 years. Your reaction?", "options": [
        ("2 years too long — I need money this season", "Present Bias"),
        ("What if it fails? My current method is safe", "Loss Aversion"),
        ("Let my neighbour try first. If successful I'll follow", "Social Proof"),
        ("I've never done organic. It won't work on my farm", "Status Quo Bias")]},
    {"id": "d8", "question": "Your crop yield was low this season. What's the main reason?", "options": [
        ("Bad weather — nothing I could have done differently", "Overconfidence"),
        ("I used the same method as last year that worked", "Anchoring"),
        ("I planted what neighbours planted — maybe wrong", "Social Proof"),
        ("I was scared to try a new fertilizer — played safe", "Status Quo Bias")]},
]


# ════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_name TEXT, question TEXT, answer TEXT,
        bias_detected TEXT, timestamp TEXT)""")
    conn.commit()
    conn.close()

def save_decision(farmer_name, question, answer, bias):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO decisions (farmer_name,question,answer,bias_detected,timestamp) VALUES (?,?,?,?,?)",
        (farmer_name, question, answer, bias, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_decisions(farmer_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT question,answer,bias_detected,timestamp FROM decisions WHERE farmer_name=? ORDER BY id DESC", (farmer_name,))
    rows = c.fetchall()
    conn.close()
    return rows

def detect_dominant_bias(farmer_name):
    rows = get_decisions(farmer_name)
    if not rows:
        return None, {}
    counts = Counter(r[2] for r in rows)
    return counts.most_common(1)[0][0], dict(counts)


# ════════════════════════════════════════════════════════════
# NUDGE — Groq LLM (FREE)
# ════════════════════════════════════════════════════════════
def get_nudge(bias, farmer_name, lang_code, api_key=""):
    if GROQ_AVAILABLE and api_key:
        try:
            client = Groq(api_key=api_key)
            lang_name = next((k for k, v in LANGUAGES.items() if v == lang_code), "Hindi")
            r = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content":
                    f"You are an empathetic advisor for Indian farmers.\n"
                    f"Farmer: {farmer_name}\nBias: {bias}\n"
                    f"Write 3-4 sentence warm nudge in {lang_name}. "
                    f"Simple language. Address by name. Output ONLY the message."}],
                max_tokens=200)
            nudge = r.choices[0].message.content.strip()
            if nudge:
                return nudge
        except Exception:
            pass
    nudge = FALLBACK_NUDGES.get(bias, "Aage badhte raho. Har din seekhne ka mauka hai.")
    if TRANSLATE_AVAILABLE and lang_code not in ["en", "hi"]:
        try:
            nudge = GoogleTranslator(source="hi", target=lang_code).translate(nudge)
        except Exception:
            pass
    return nudge


# ════════════════════════════════════════════════════════════
# EMAIL — Brevo SMTP (FREE 300 emails/day, no credit card)
# ════════════════════════════════════════════════════════════
def send_email_nudge(to_email, farmer_name, bias, nudge_text):
    if not all([BREVO_SMTP_LOGIN, BREVO_SMTP_KEY, EMAIL_FROM]):
        return False, "Brevo not configured. Add BREVO_SMTP_LOGIN, BREVO_SMTP_KEY, EMAIL_FROM to .env"
    try:
        info = BIAS_INFO.get(bias, {})
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your Farming Nudge — {bias}"
        msg["From"]    = f"Farmer Behavioral Twin <{EMAIL_FROM}>"
        msg["To"]      = to_email
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;
                    background:#F0EAD6;border-radius:12px;overflow:hidden;">
          <div style="background:#1B3A2D;padding:24px;">
            <h2 style="color:#C8973A;margin:0;">🌾 Farmer Behavioral Twin</h2>
          </div>
          <div style="padding:28px;">
            <p style="color:#1B3A2D;">Namaste <b>{farmer_name}</b>,</p>
            <div style="background:#1B3A2D;border-left:5px solid #C8973A;
                        border-radius:8px;padding:20px;margin:16px 0;">
              <p style="color:white;font-size:16px;line-height:1.7;margin:0;">{nudge_text}</p>
            </div>
            <p style="color:#555;font-size:13px;margin-top:16px;">
              {info.get('emoji','')} <b>{bias}</b>: {info.get('desc','')}
            </p>
          </div>
          <div style="background:#2D5A3D;padding:12px;text-align:center;">
            <p style="color:#A8C5B0;font-size:11px;margin:0;">
              Farmer Behavioral Twin · Jain University Hackathon · Rs.0/month
            </p>
          </div>
        </div>"""
        msg.attach(MIMEText(nudge_text, "plain"))
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP("smtp-relay.brevo.com", 587) as s:
            s.starttls()
            s.login(BREVO_SMTP_LOGIN, BREVO_SMTP_KEY)
            s.sendmail(EMAIL_FROM, to_email, msg.as_string())
        return True, f"Nudge sent to {to_email}"
    except Exception as e:
        return False, f"Email failed: {str(e)}"


# ════════════════════════════════════════════════════════════
# VOICE — gTTS (FREE)
# ════════════════════════════════════════════════════════════
def speak(text, lang_code):
    if not TTS_AVAILABLE:
        return None
    try:
        gTTS(text=text, lang=lang_code, slow=False).save("nudge_audio.mp3")
        with open("nudge_audio.mp3", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


# ════════════════════════════════════════════════════════════
# STREAMLIT UI
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Farmer Behavioral Twin",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""<style>
.stApp { background: #F0EAD6; }
.bias-card { background: white; border-radius: 12px; padding: 20px; margin: 8px 0;
             border-left: 5px solid #C8973A; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
.nudge-box { background: #1B3A2D; color: white; border-radius: 16px; padding: 28px;
             font-size: 18px; line-height: 1.7; margin: 20px 0; border-left: 6px solid #C8973A; }
.stat-box  { background: #1B3A2D; color: white; border-radius: 12px;
             padding: 20px; text-align: center; }
.stat-num  { font-size: 42px; font-weight: bold; color: #C8973A; }
.stat-label{ font-size: 13px; color: #A8C5B0; }
.q-box     { background: white; border-radius: 12px; padding: 24px;
             box-shadow: 0 2px 12px rgba(0,0,0,.08); margin: 16px 0; }
.free-tag  { background: #27AE60; color: white; border-radius: 20px;
             padding: 2px 9px; font-size: 11px; font-weight: bold; }
h1 { color: #1B3A2D !important; }
h2, h3 { color: #2D5A3D !important; }
.stButton > button { background: #1B3A2D; color: white; border-radius: 8px;
                     border: none; padding: 10px 24px; font-size: 15px; }
.stButton > button:hover { background: #C8973A; }
</style>""", unsafe_allow_html=True)

init_db()

# ── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌾 Farmer Behavioral Twin")
    st.markdown("---")
    farmer_name  = st.text_input("👤 Your Name", placeholder="e.g. Ramesh Kumar")
    lang_choice  = st.selectbox("🗣️ Language", list(LANGUAGES.keys()))
    lang_code    = LANGUAGES[lang_choice]
    st.markdown("---")
    st.markdown("**🔑 Free API Keys**")
    api_key      = st.text_input("Groq API Key", type="password",
                                  placeholder="console.groq.com — free",
                                  value=GROQ_API_KEY)
    farmer_email = st.text_input("📧 Your Email", placeholder="for nudge delivery — optional")
    st.markdown("---")
    page = st.radio("📍 Navigate", ["🏠 Home", "📝 Assessment", "🧠 Bias Profile", "💡 Get Nudge"])
    st.markdown("---")
    st.markdown("**✅ Service Status**")
    st.markdown(f"{'🟢' if api_key else '🔴'} Groq LLM (AI nudges)")
    st.markdown(f"{'🟢' if BREVO_SMTP_LOGIN else '🔴'} Brevo Email (300/day free)")
    st.markdown(f"{'🟢' if TTS_AVAILABLE else '🔴'} Voice — gTTS")
    st.markdown(f"{'🟢' if TRANSLATE_AVAILABLE else '🔴'} Translator")

# ── GATE: name required ──────────────────────────────────
if not farmer_name:
    st.markdown("# 🌾 Farmer Behavioral Twin")
    st.info("👈 Enter your name in the sidebar to begin.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""<div class='bias-card'><h3>What is this?</h3>
        <p>Every farming AI tells farmers <b>what to do</b>.<br>
        We understand <b>why they don't do it</b> — and fix that.<br><br>
        Detects cognitive biases → personalised nudges in your language via voice + email.</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class='bias-card'><h3>💰 Total Cost</h3>
        <p>🟢 Groq API — Free forever<br>
           🟢 Brevo Email — 300/day free (no card)<br>
           🟢 Voice gTTS — Free forever<br>
           🟢 Translator — Free forever<br>
           🟢 SQLite DB — Free forever<br><br>
           <b>Total: Rs.0 / month</b></p>
        </div>""", unsafe_allow_html=True)
    st.stop()


# ════════════════════════════════════════════════════════════
# PAGE: HOME
# ════════════════════════════════════════════════════════════
if "🏠 Home" in page:
    st.markdown(f"# 🌾 Namaste, {farmer_name}!")
    st.markdown("### Your AI that understands HOW you think — not just WHAT to do.")
    st.markdown("---")
    rows = get_decisions(farmer_name)
    dominant, counts = detect_dominant_bias(farmer_name)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='stat-box'><div class='stat-num'>{len(rows)}</div><div class='stat-label'>Decisions Logged</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='stat-box'><div class='stat-num'>{len(counts)}</div><div class='stat-label'>Biases Found</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='stat-box'><div class='stat-num'>{len(DECISIONS)}</div><div class='stat-label'>Questions</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='stat-box'><div class='stat-num'>12</div><div class='stat-label'>Languages</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🧬 6 Biases We Detect")
    cols = st.columns(3)
    for i, (bias, info) in enumerate(BIAS_INFO.items()):
        with cols[i % 3]:
            st.markdown(
                f"<div class='bias-card' style='border-left-color:{info['color']}'>"
                f"<b>{info['emoji']} {bias}</b><br><small>{info['desc']}</small></div>",
                unsafe_allow_html=True)
    if dominant:
        st.markdown("---")
        st.info(f"🔍 Dominant bias so far: **{BIAS_INFO[dominant]['emoji']} {dominant}** — go to Get Nudge.")


# ════════════════════════════════════════════════════════════
# PAGE: ASSESSMENT
# ════════════════════════════════════════════════════════════
elif "📝 Assessment" in page:
    st.markdown("# 📝 Quick Assessment")
    st.markdown("No right or wrong answers. Takes 2 minutes.")
    st.markdown("---")
    if "q_index" not in st.session_state:
        st.session_state.q_index = 0
    q_idx = st.session_state.q_index
    if q_idx >= len(DECISIONS):
        st.success(f"✅ Done! {len(DECISIONS)} questions answered.")
        st.balloons()
        dominant, _ = detect_dominant_bias(farmer_name)
        if dominant:
            info = BIAS_INFO[dominant]
            st.markdown(
                f"<div class='nudge-box'><b>{info['emoji']} Dominant Bias: {dominant}</b>"
                f"<br><br>{info['desc']}</div>", unsafe_allow_html=True)
        if st.button("🔄 Retake Assessment"):
            st.session_state.q_index = 0
            st.rerun()
        st.stop()
    q = DECISIONS[q_idx]
    st.progress(q_idx / len(DECISIONS), text=f"Question {q_idx + 1} of {len(DECISIONS)}")
    st.markdown(f"<div class='q-box'><h3>❓ {q['question']}</h3></div>", unsafe_allow_html=True)
    choice = st.radio("Your most likely response:", [o[0] for o in q["options"]], key=f"q_{q_idx}")
    if st.button("Submit Answer →"):
        bias = next(b for o, b in q["options"] if o == choice)
        save_decision(farmer_name, q["question"], choice, bias)
        st.session_state.q_index += 1
        st.rerun()


# ════════════════════════════════════════════════════════════
# PAGE: BIAS PROFILE
# ════════════════════════════════════════════════════════════
elif "🧠 Bias Profile" in page:
    st.markdown(f"# 🧠 Bias Profile: {farmer_name}")
    rows = get_decisions(farmer_name)
    if not rows:
        st.warning("No decisions yet. Take the assessment first!")
        st.stop()
    dominant, counts = detect_dominant_bias(farmer_name)
    st.markdown(f"### Based on **{sum(counts.values())}** decisions")
    st.markdown("---")
    import plotly.graph_objects as go
    sb = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    fig = go.Figure(go.Bar(
        x=[v for _, v in sb], y=[b for b, _ in sb], orientation="h",
        marker_color=[BIAS_INFO[b]["color"] for b, _ in sb],
        text=[f"{v} times" for _, v in sb], textposition="outside"))
    fig.update_layout(
        title="Your Bias Distribution", paper_bgcolor="#F0EAD6", plot_bgcolor="#F0EAD6",
        font=dict(color="#1B3A2D"), height=320, margin=dict(l=10, r=60, t=40, b=10),
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    st.markdown("### 📋 Decision History")
    for q, a, b, ts in rows:
        info = BIAS_INFO.get(b, {"emoji": "❓", "color": "#999"})
        st.markdown(
            f"<div class='bias-card' style='border-left-color:{info['color']}'>"
            f"<b>{info['emoji']} {b}</b> <small style='color:#888'>{ts[:16]}</small><br>"
            f"<small><b>Q:</b> {q}</small><br>"
            f"<small style='color:#555'><b>A:</b> {a}</small></div>",
            unsafe_allow_html=True)
    if st.button("🗑️ Clear My Data"):
        conn = sqlite3.connect(DB_FILE)
        conn.execute("DELETE FROM decisions WHERE farmer_name=?", (farmer_name,))
        conn.commit()
        conn.close()
        st.success("Data cleared.")
        st.rerun()


# ════════════════════════════════════════════════════════════
# PAGE: GET NUDGE
# ════════════════════════════════════════════════════════════
elif "💡 Get Nudge" in page:
    st.markdown("# 💡 Your Personalised Nudge")
    rows = get_decisions(farmer_name)
    if not rows:
        st.warning("Complete the assessment first!")
        st.stop()
    dominant, _ = detect_dominant_bias(farmer_name)
    info = BIAS_INFO[dominant]
    st.markdown(f"### {info['emoji']} Detected: **{dominant}**")
    st.caption(info["desc"])
    st.markdown("---")
    with st.spinner("🧠 Generating nudge..."):
        nudge = get_nudge(dominant, farmer_name, lang_code, api_key)
    st.markdown(f"<div class='nudge-box'>{nudge}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🔊 Voice Audio** <span class='free-tag'>FREE</span>", unsafe_allow_html=True)
        if TTS_AVAILABLE:
            if st.button(f"▶ Listen in {lang_choice}"):
                with st.spinner("Generating audio..."):
                    a64 = speak(nudge, lang_code)
                if a64:
                    st.markdown(
                        f'<audio autoplay controls><source src="data:audio/mp3;base64,{a64}" type="audio/mp3"></audio>',
                        unsafe_allow_html=True)
                else:
                    st.warning("Audio needs internet connection.")
        else:
            st.caption("Run: `pip install gtts`")
    with c2:
        st.markdown("**📧 Email Nudge** <span class='free-tag'>FREE · Brevo · 300/day</span>", unsafe_allow_html=True)
        if farmer_email:
            if st.button("📨 Send to my Email"):
                if BREVO_SMTP_LOGIN and BREVO_SMTP_KEY:
                    with st.spinner("Sending..."):
                        ok, msg = send_email_nudge(farmer_email, farmer_name, dominant, nudge)
                    (st.success if ok else st.error)(msg)
                else:
                    st.warning("""Brevo not set up yet. 5-min free setup:
1. brevo.com → Sign up free (no card needed)
2. Settings → SMTP & API → Generate SMTP Key
3. Add to your .env:
```
BREVO_SMTP_LOGIN=you@email.com
BREVO_SMTP_KEY=your-key
EMAIL_FROM=you@email.com
```
4. Restart the app""")
        else:
            st.caption("Enter your email in the sidebar to enable.")
    st.markdown("---")
    st.markdown("### 📚 All 6 Nudge Cards")
    for bias, binfo in BIAS_INFO.items():
        with st.expander(f"{binfo['emoji']} {bias}"):
            st.write(FALLBACK_NUDGES.get(bias, ""))