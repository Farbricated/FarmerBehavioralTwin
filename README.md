# 🌾 Farmer Behavioral Twin

> *Every farming AI tells farmers **what to do**.*
> *We are the first to understand **why they don't do it** — and fix that.*

An AI-powered web app that detects the hidden cognitive biases of Indian farmers through scenario-based questions and delivers personalised nudges in their own language via voice and email — at zero cost.

Built for the **National Hackathon: Tech for Agriculture** · Jain (Deemed-to-be University), Bengaluru · In association with IBM.

---

## 📸 What It Does

```
Farmer answers 8 quick scenarios
        ↓
AI detects dominant cognitive bias (out of 6)
        ↓
LLM generates personalised nudge (Groq — free)
        ↓
Voice audio plays in farmer's language (gTTS — free)
        ↓
Nudge delivered to email (Brevo SMTP — free)
```

---

## 🧠 The 6 Biases Detected

| Bias | What It Means |
|------|---------------|
| 🛡️ Loss Aversion | Refuses better options due to fear of change |
| ⏰ Present Bias | Always picks short-term money over long-term profit |
| ⚓ Anchoring | Stuck on last year's price for every decision |
| 👥 Social Proof | Copies neighbours regardless of own farm conditions |
| 💪 Overconfidence | Ignores weather/market warnings, trusts gut only |
| 🔒 Status Quo Bias | Refuses any new technique or technology |

---

## 💰 All Free — Zero Cost Stack

| Service | Use | Free Tier |
|---------|-----|-----------|
| [Groq API](https://console.groq.com) | LLM nudge generation (Llama3) | Free forever |
| [Brevo SMTP](https://brevo.com) | Email nudge delivery | 300 emails/day, no card |
| gTTS | Voice audio in 12 languages | Free forever |
| deep-translator | Regional language translation | Free forever |
| SQLite | Local farmer decision database | Built into Python |
| Streamlit | Web UI | Free forever |
| **Total** | | **Rs. 0 / month** |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/yourname/farmer-behavioral-twin.git
cd farmer-behavioral-twin
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your free API keys
```bash
cp .env.example .env
```
Open `.env` and fill in:
```env
GROQ_API_KEY=your_key_here          # console.groq.com → free signup
BREVO_SMTP_LOGIN=you@email.com      # brevo.com → free signup
BREVO_SMTP_KEY=your_smtp_key        # Settings → SMTP & API → Generate Key
EMAIL_FROM=you@email.com
```

### 4. Run the app
```bash
streamlit run main.py
```

App opens at → **http://localhost:8501**

---

## 🔑 Getting Free API Keys

### Groq API (2 minutes)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up with Google — no credit card
3. Click **API Keys** → **Create API Key**
4. Copy and paste into `.env`

### Brevo SMTP (5 minutes)
1. Go to [brevo.com](https://brevo.com) → Sign up free
2. Go to **Settings** → **SMTP & API**
3. Click **Generate new SMTP key**
4. Copy **SMTP Login** (your email) + **SMTP Key** into `.env`

---

## 📁 Project Structure

```
farmer-behavioral-twin/
├── main.py              # Entire app — UI + ML + AI + Voice + Email + DB
├── requirements.txt     # 6 Python packages
├── .env                 # Your secret keys (never commit this)
├── .env.example         # Safe template to commit
├── .gitignore           # Protects .env and DB from being committed
├── README.md            # This file
└── farmer_twin.db       # Auto-created SQLite DB on first run
```

---

## 🖥️ App Pages

**🏠 Home** — Stats dashboard + overview of all 6 biases

**📝 Assessment** — 8 real-world farming scenario questions, one at a time

**🧠 Bias Profile** — Plotly bar chart of your bias distribution + full decision history

**💡 Get Nudge** — AI-generated personalised nudge in your language + voice playback + email delivery

---

## 🌐 Languages Supported

English · Hindi · Kannada · Tamil · Telugu · Marathi · Bengali · Gujarati · Punjabi · Malayalam · Odia · Assamese

Works on **2G networks**. Voice-first — no literacy required.

---

## 🏆 Hackathon Details

| | |
|---|---|
| **Event** | National Hackathon: Tech for Agriculture |
| **Host** | Jain (Deemed-to-be University), Bengaluru |
| **Partner** | IBM |
| **Theme** | AI for Zero Hunger · Sustainable Supply Chains · Smart Price Prediction |
| **Prize Pool** | ₹1,50,000 |

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first.

---

*Built with ❤️ for Indian farmers.*