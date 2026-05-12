# EduAI Nexus — Python Backend
**Team MAHADEV · WitchHunt Hackathon 2026 · Education Theme**  
Jayashree H N (Team Lead) · Roshini D

---

## 🚀 Quick Start

```bash
# 1. Clone & setup
git clone https://github.com/your-team/eduai-nexus-backend
cd eduai-nexus-backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env
# Edit .env and add your keys (see below)

# 3. Run
uvicorn main:app --reload --port 8000

# 4. Open Swagger docs
open http://localhost:8000/docs
```

---

## 🔑 API Keys (all free)

| Variable | Where to get | Free limit |
|---|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | 1M tokens/day |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | 14,400 req/day |
| `NEWSDATA_API_KEY` | [newsdata.io](https://newsdata.io) | 200 req/day |
| `SUPABASE_URL` + `SUPABASE_ANON_KEY` | [supabase.com](https://supabase.com) | 500MB free |
| `UPSTASH_REDIS_URL` + `UPSTASH_REDIS_TOKEN` | [upstash.com](https://upstash.com) | 10K cmd/day |
| `BHASHINI_API_KEY` + `BHASHINI_USER_ID` | [bhashini.gov.in](https://bhashini.gov.in) | Unlimited (education) |

> Only `GEMINI_API_KEY` is required to run the POC. All others are optional fallbacks.

---

## 📦 Project Structure

```
eduai-nexus-backend/
├── main.py                  # FastAPI entry point
├── requirements.txt
├── .env.example
├── routers/
│   ├── learn.py             # Module 1: Personalised Learning
│   ├── labs.py              # Module 2: Virtual Labs
│   ├── translate.py         # Module 3: Multilingual
│   ├── career.py            # Module 4: Career Readiness
│   ├── dashboard.py         # Module 5: Resource Allocation
│   └── projects.py          # Module 6: Micro-Projects
├── services/
│   ├── gemini.py            # Google Gemini 1.5 Flash wrapper
│   ├── groq_ai.py           # Groq/Llama 3.1 8B wrapper
│   ├── bhashini.py          # Bhashini translation wrapper
│   └── news.py              # NewsData.io wrapper
└── db/
    └── supabase_client.py   # Supabase PostgreSQL client
```

---

## 🗂 API Endpoints

### Module 1 — Personalised Learning `/api/v1/learn`
| Method | Path | Description |
|---|---|---|
| POST | `/generate-mcqs` | Generate MCQs from any text |
| POST | `/flashcards` | Generate study flashcards |
| POST | `/summarise` | Summarise educational content |
| POST | `/explain` | Explain a concept at grade level |

### Module 2 — Virtual Labs `/api/v1/labs`
| Method | Path | Description |
|---|---|---|
| POST | `/explain` | Run a simulation + get AI explanation |
| GET | `/list` | All available labs |
| POST | `/quiz` | Post-lab quiz questions |

### Module 3 — Multilingual `/api/v1/translate`
| Method | Path | Description |
|---|---|---|
| POST | `/concept` | Translate + simplify a concept |
| GET | `/flashnews` | Current affairs cards in target language |
| GET | `/languages` | Supported languages list |
| POST | `/batch` | Translate multiple terms at once |

### Module 4 — Career Readiness `/api/v1/career`
| Method | Path | Description |
|---|---|---|
| POST | `/ats-analyze` | ATS score + keyword analysis |
| POST | `/skill-gap` | Skill gaps for a career goal |
| POST | `/chat` | AI career counsellor chat |
| GET | `/careers` | Popular Indian career paths |
| POST | `/roadmap` | 6-month learning roadmap |

### Module 5 — Resource Allocation `/api/v1/dashboard`
| Method | Path | Description |
|---|---|---|
| GET | `/district-data` | KPIs + forecast for a district |
| GET | `/all-districts` | All districts overview |
| POST | `/simulate-policy` | AI policy impact prediction |
| GET | `/state-summary` | Karnataka aggregate stats |
| POST | `/recommend-action` | AI intervention recommendation |

### Module 6 — Micro-Projects `/api/v1/projects`
| Method | Path | Description |
|---|---|---|
| POST | `/generate` | 3 personalised project ideas |
| GET | `/opportunities` | Hackathons & internships |
| GET | `/interests` | Supported interest areas |
| POST | `/breakdown` | Week-by-week task breakdown |

---

## ☁️ Deploy to Railway (free)

```bash
npm install -g @railway/cli
railway login
railway init
railway up
railway variables set GEMINI_API_KEY=your_key
railway variables set GROQ_API_KEY=your_key
# add all .env variables
railway domain
# ✅ Live at: https://eduai-nexus-backend.up.railway.app
```

Then update Lovable's `.env.local`:
```
VITE_BACKEND_URL=https://eduai-nexus-backend.up.railway.app
```

---

## ✅ POC Acceptance Checklist

- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `GET /docs` shows all endpoints in Swagger UI
- [ ] `POST /api/v1/learn/generate-mcqs` returns 5 MCQ questions
- [ ] `POST /api/v1/labs/explain` returns physics formula + explanation
- [ ] `POST /api/v1/translate/concept` returns translated + simplified text
- [ ] `POST /api/v1/career/ats-analyze` returns score + missing keywords
- [ ] `POST /api/v1/career/chat` returns career advice
- [ ] `GET /api/v1/dashboard/district-data?district=Kalaburagi` shows shortage alert
- [ ] `POST /api/v1/projects/generate` returns 3 project ideas
- [ ] No CORS errors when called from Lovable frontend
- [ ] Zero paid API calls (all free tier)
- [ ] No API keys in source code (all in `.env`)

---

*EduAI Nexus · Team MAHADEV · WitchHunt Hackathon 2026*
