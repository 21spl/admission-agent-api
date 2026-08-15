# Admission Agent API

An async, production-grade admissions management platform with an AI-driven 
document verification and shortlisting pipeline. Built as a portfolio 
demonstration of full-stack backend engineering, multi-agent RAG systems, and 
secure API design.

## Overview

Handles the end-to-end admissions lifecycle — application submission, document 
upload and AI-assisted verification, officer review workflows, and automated 
shortlisting — behind a role-based, JWT-secured API.

## Tech Stack

**Backend:** FastAPI (async), SQLAlchemy 2.0 (async), Alembic, Pydantic v2, asyncpg

**Database:** Neon PostgreSQL + pgvector

**AI / RAG:** LlamaIndex (multi-agent Workflows), Google Gemini (LLM + embeddings)

**Storage:** Filebase (S3-compatible)

**Email:** Brevo REST API

**Auth:** JWT (PyJWT) + passlib/bcrypt, RBAC

**Frontend:** Streamlit

**Testing:** pytest, httpx AsyncClient, isolated Neon branch per CI run

**CI/CD:** GitHub Actions → Render (backend, Docker) + Streamlit Community Cloud (frontend)

## Architecture Highlights

- **Layered design** — repository → service → router separation; 
- **Gale-Shapley based shortlisting algorithm** for stable applicant-seat matching 
  across multiple counselling rounds.
- **Document validation** isn't fully automated. Al handles the clear cases, but gray-zone documents get routed to a **human-in-the-loop review**, where an admin makes the final call. Al assists; it doesn't decide unilaterally.
- Student support runs on **multi-agent orchestration** - service methods are wrapped as **DB query tools** for personalized queries (status, application details), while policy-based questions are handled through RAG. The agents route to the right tool depending on what's actually being asked.
- **pgvector** chosen over a standalone vector DB to keep applicant data and embeddings in one transactional store.
- **Ethical scoping**: eligibility/rank prediction was deliberately excluded from 
  an official admissions system — predictive scoring on individual applicants 
  raises fairness and accountability concerns unsuitable for a real institutional 
  workflow.

Design rationale for these choices, including trade-offs considered, is recorded 
in [`decisions.md`](docs/decisions.md).

## Project Structure

```bash
admission-agent-api/ 
├── app/                # FastAPI backend
├── streamlit_app/       # Streamlit frontend
├── alembic/             # DB migrations
├── tests/               # pytest suite (unit + integration)
├── Dockerfile
```

## Getting Started

```bash
git clone https://github.com/21spl/University-Admission-AI.git
cd University-Admission-AI

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set required environment variables (see .env.example)
# DATABASE_URL, GEMINI_API_KEY, FILEBASE_KEY/SECRET, BREVO_API_KEY, JWT_SECRET, etc.

alembic upgrade head
uvicorn app.main:app --reload
```

Interactive API docs (Swagger) are available at `/docs` once running locally, or 
at the deployed URL below.

## Deployment

Backend: Dockerized, deployed on Render (Ohio/us-east region, matching Neon).

Frontend: Streamlit Community Cloud.

DB: Neon Postgres, pooled connection in production.

Backend URL: https://admission-agent-api.onrender.com
([API docs](https://admission-agent-api.onrender.com/docs))

Frontend URL: https://admission-agent-frontend.streamlit.app

## Documentation

Detailed architecture and implementation documentation is available in the 
[`docs/`](docs/) directory.

| Document | Description |
|---|---|
| [`agent-orchestration.md`](docs/agent-orchestration.md) | Multi-agent architecture, orchestration, tools, and RAG ingestion workflow |
| [`document-validation.md`](docs/document-validation.md) | AI-assisted document validation pipeline and workflow |
| [`domain-model.md`](docs/domain-model.md) | Domain entities, relationships, and database model |
| [`shortlisting.md`](docs/shortlisting.md) | Shortlisting algorithm, counselling rounds, seat allocation, and offer rules |
| [`security.md`](docs/security.md) | Discovered vulnerability, impact, and remediation |
| [`decisions.md`](docs/decisions.md) | Architecture Decision Records — key trade-offs and reasoning |

## License

Portfolio project — not licensed for reuse.