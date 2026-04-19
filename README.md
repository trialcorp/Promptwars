# 🌟 VenueFlow — AI-Powered Crowd Intelligence for Live Events

> *by [volunteer.media](https://volunteer.media)*

A crowd-sourced intelligence platform that transforms chaotic, real-time observations from stadium attendees into structured, actionable guidance — like **"Waze for stadiums"**, powered by Gemini AI.

## Challenge Vertical

**Physical Event Experience** — Improving the attendee experience at large-scale sporting venues by addressing crowd movement, waiting times, and real-time coordination.

## Approach & Logic

At a 50,000-person IPL match, every attendee already knows something useful — "Gate D has no queue", "Food Court 2 is packed", "Parking Lot B is full." But this knowledge is trapped in individual heads.

**VenueFlow unlocks this collective intelligence.** Every attendee becomes a voluntary sensor. They report what they see in any language, and Gemini AI aggregates this crowd-sourced chaos into a live intelligence feed that benefits everyone.

### How It Works

1. **Report** — Attendees submit observations in any of 6 Indian languages (Hindi, Telugu, Tamil, Kannada, Marathi, English). Input can be informal, messy, social-media style.
2. **Detect Language** — Cloud Translate v3 auto-detects the input language.
3. **Translate to English** — Input is translated to English for Gemini processing (highest accuracy).
4. **AI Analysis** — Gemini 2.5 Flash classifies the report: type (CROWD/FOOD/PARKING/WEATHER/SAFETY), severity, location, crowd density, wait times, and generates actionable recommendations with alternatives.
5. **Translate Response Back** — The **entire structured response** is translated back to the user's detected language. If you report in Hindi, you get the full response in Hindi.
6. **Store & Share** — Report metadata stored in Firestore, full report archived in Cloud Storage. All reports feed into a live crowd pulse visible to every attendee.

### Key Differentiators

- **Crowd-sourced, not single-user** — Every report improves the experience for everyone
- **Full language round-trip** — Input AND output in the user's language (not just input translation)
- **Safety-first** — Stampede risk, medical emergencies, weather alerts elevated automatically
- **Real-time feed** — Live pulse of venue conditions from crowd reports
- **Indian context** — IPL, ISL, PKL venue awareness with India-specific emergency contacts

## Project Structure

```
├── main.py                          # Entry point (minimal)
├── app/
│   ├── __init__.py                  # Flask app factory
│   ├── config.py                    # Centralized configuration
│   ├── security.py                  # Headers, rate limiting, sanitization
│   ├── cache.py                     # In-memory response cache
│   ├── analysis.py                  # Gemini system prompt & analysis
│   ├── models/
│   │   ├── __init__.py
│   │   └── report.py               # CrowdReport data model
│   └── services/
│       ├── __init__.py              # Service registry
│       ├── gemini.py                # Vertex AI + Gemini client
│       ├── translate.py             # Cloud Translate v3 (with response translation)
│       ├── firestore_client.py      # Firestore operations
│       ├── storage.py               # Cloud Storage operations
│       ├── logging_client.py        # Cloud Logging
│       └── secrets.py               # Secret Manager
├── templates/
│   └── index.html                   # UI (Report, Live Feed, About tabs)
├── tests/
│   ├── __init__.py
│   └── test_app.py                  # 65+ unit tests
├── Dockerfile                       # Multi-stage production build
├── requirements.txt
└── README.md
```

## Google Services Used

| # | Service | Module | Purpose |
|---|---------|--------|---------|
| 1 | **Vertex AI** | `services/gemini.py` | AI/ML platform initialization |
| 2 | **Gemini 2.5 Flash** | `analysis.py` | Crowd report classification & recommendations |
| 3 | **Cloud Translate v3** | `services/translate.py` | Multilingual I/O — detect, translate input, translate full response back |
| 4 | **Cloud Firestore** | `services/firestore_client.py` | Real-time crowd reports database + zone stats |
| 5 | **Cloud Storage** | `services/storage.py` | Full report JSON archival |
| 6 | **Secret Manager** | `services/secrets.py` | Secure API key retrieval |
| 7 | **Cloud Logging** | `services/logging_client.py` | Production monitoring |
| 8 | **Cloud Run** | `Dockerfile` | Serverless container deployment |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI with Report, Live Feed, and About tabs |
| `/report` | POST | Submit a crowd report → AI-analyzed structured guidance |
| `/translate` | POST | Translate text via Cloud Translate v3 |
| `/feed` | GET | Live feed of recent crowd reports from Firestore |
| `/zones` | GET | Venue zone density statistics |
| `/health` | GET | Service health dashboard |

## Key Features

- **Crowd intelligence network** — crowd-sourced reports aggregated by AI
- **Full language round-trip** — response in the SAME language as input
- **6 Indian languages** — Hindi, Telugu, Tamil, Kannada, Marathi, English
- **Report classification** — CROWD, FOOD, PARKING, WEATHER, SAFETY, FACILITY, NAVIGATION
- **Severity levels** — CRITICAL, HIGH, MODERATE, LOW, INFO
- **Alternative suggestions** — less crowded options near reported locations
- **Safety alerts** — automatic elevation for stampede risk, medical, weather
- **Live feed** — real-time venue pulse from all attendees
- **Wait time estimates** — AI-predicted queue durations
- **Response caching** — 2-min TTL for real-time relevance
- **Rate limiting** — 30 req/min per IP
- **Security headers** — CSP, HSTS, XSS, Frame-Options, Permissions-Policy
- **Error handlers** — JSON responses for 404, 405, 500
- **Non-root Docker** — multi-stage build, unprivileged user
- **65+ unit tests** — routes, security, cache, models, config, sanitization
- **WCAG accessible** — skip links, ARIA labels, keyboard navigation, reduced motion

## Assumptions

- Attendees have mobile internet at the venue
- Input is text-based observations
- Venue layout follows typical Indian stadium patterns (gates, stands, food courts, parking lots)
- Emergency contacts are India-specific (Police: 100, Ambulance: 108, Fire: 101)

## Local Development

1. **Setup Environment:**
   ```bash
   pip install -r requirements.txt
   cp .env.template .env
   # Edit .env with your Google Cloud project details and Gemini API Key
   ```

2. **Run Application:**
   ```bash
   python main.py
   ```

3. **Visit:** `http://localhost:8080`

## Testing

```bash
pip install pytest
python -m pytest tests/ -v
```

## Deploy to Cloud Run

```bash
gcloud run deploy venueflow \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id \
  --memory=512Mi --timeout=120
```
