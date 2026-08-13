# Admission Agent API

An async, production-grade admissions management platform with an AI-driven document verification and shortlisting pipeline. Built as a portfolio demonstration of full-stack backend engineering, multi-agent RAG systems, and secure API design.

## Overview

Handles the end-to-end admissions lifecycle — application submission, document upload and AI-assisted verification, officer review workflows, and automated shortlisting — behind a role-based, JWT-secured API.

## Tech Stack

**Backend:** 
FastAPI (async), SQLAlchemy 2.0 (async), Alembic, Pydantic v2, asyncpg

**Database:** Neon PostgreSQL + pgvector

**AI / RAG:** LlamaIndex (multi-agent Workflows), Google Gemini (LLM + embeddings)


**Storage:** Filebase (S3-compatible)

**Email:** Brevo REST API

**Auth:** JWT (PyJWT) + passlib/bcrypt, RBAC

**Frontend:** Streamlit

**Testing:** pytest, httpx AsyncClient, isolated Neon branch per CI run

**CI/CD:** GitHub Actions → Render (backend, Docker) + Streamlit Community Cloud (frontend)

## Architecture Highlights

- **Layered design** — strict repository → service → router separation; no raw queries bypassing repositories.
- **Multi-agent RAG pipeline** for document validation, orchestrated with LlamaIndex AgentWorkflow.
- **Gale-Shapley based shortlisting algorithm** for stable applicant-seat matching.
- **pgvector** chosen over a standalone vector DB to keep applicant data and embeddings in one transactional store.
- **Ethical scoping**: eligibility/rank prediction was deliberately excluded from an official admissions system — predictive scoring on individual applicants raises fairness and accountability concerns unsuitable for a real institutional workflow.

## Project Structure

admission-agent-api/ 
├── app/                # FastAPI backend
├── streamlit_app/       # Streamlit frontend
├── alembic/             # DB migrations
├── tests/               # pytest suite (unit + integration)
├── Dockerfile


## Deployment
Backend: Dockerized, deployed on Render (Ohio/us-east region, matching Neon).
Frontend: Streamlit Community Cloud.
DB: Neon Postgres, pooled connection in production.

Backend URL: https://admission-agent-api.onrender.com
Frontend URL: https://admission-agent-frontend.streamlit.app
