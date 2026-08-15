# Architecture Decision Records

## ADR-001: pgvector over a standalone vector database

**Context:** The RAG pipeline needs vector similarity search for document embeddings 
alongside the relational admissions data.

**Decision:** Use pgvector inside the existing Neon PostgreSQL instance rather than 
running a separate vector store (e.g. ChromaDB, Pinecone).

**Reasoning:**
- Applicant records and their document embeddings are transactionally related — 
  keeping them in one database means one connection pool, one backup story, and 
  no cross-store consistency problem.
- Avoids operating a second stateful service for a portfolio-scale project where 
  the operational overhead of a separate vector DB isn't justified by the data volume.
- SQLAlchemy already owns the schema; extending it with a vector column is simpler 
  than maintaining a second ORM/client for a different store.

**Trade-off accepted:** pgvector is less feature-rich than a dedicated vector DB 
(no built-in hybrid search tooling, fewer indexing strategies at scale). Acceptable 
because query volume and corpus size are both small.

## ADR-002: Gale-Shapley deferred acceptance over greedy allocation

**Context:** Seat allocation must match applicants to seats fairly across multiple 
counselling rounds.

**Decision:** Implement deferred acceptance (Gale-Shapley) instead of a greedy, 
first-come-first-served or single-pass ranking allocation.

**Reasoning:**
- Greedy allocation locks in early matches that can be suboptimal once later, 
  stronger applicants are considered — deferred acceptance produces a stable 
  matching where no applicant-seat pair would both prefer each other over their 
  current match.
- Multi-round counselling is a natural fit for the iterative propose-reject 
  structure of the algorithm.

**Trade-off accepted:** The implementation deviates from textbook Gale-Shapley by 
making acceptance irrevocable between rounds (a real institutional constraint — 
students can't be un-admitted once confirmed). This means "floating" is a real 
risk: rejecting an offer isn't a guaranteed upgrade, since a stronger candidate 
who rejects can end up with nothing while a weaker candidate secures that seat. 
This is a deliberate deviation, not an oversight, and it's the first thing worth 
raising if asked "is this really Gale-Shapley?"

## ADR-003: No eligibility or rank prediction

**Context:** An AI-driven admissions system could plausibly include a model that 
predicts an applicant's chance of admission or ranks them algorithmically.

**Decision:** Explicitly excluded from scope.

**Reasoning:**
- Predictive scoring of individual applicants in a real institutional workflow 
  raises fairness and accountability concerns — a false negative silently 
  costs someone a seat, and the decision is hard to audit or contest.
- The project's AI usage is scoped to document validation (verifying submitted 
  documents against requirements) and RAG-based information retrieval — both are 
  assistive and auditable, not decision-making about a person's admission outcome.

**Trade-off accepted:** A "smarter" feature was left out on purpose. This is framed 
as a design choice, not a missing feature, when discussed.

## ADR-004: Async-first throughout

**Context:** FastAPI supports both sync and async request handling.

**Decision:** Async end-to-end — FastAPI async routes, SQLAlchemy 2.0 async engine, 
asyncpg driver, boto3 calls wrapped via `asyncio.to_thread`.

**Reasoning:**
- The workload is I/O-bound (DB queries, external API calls to Gemini, Filebase, 
  Brevo) rather than CPU-bound, which is exactly where async concurrency pays off — 
  the event loop can serve other requests while waiting on I/O instead of blocking 
  a worker thread per request.
- Consistency: mixing sync and async DB access in the same codebase is a common 
  source of `MissingGreenlet` errors from accidental lazy loading; committing to 
  async-only removes that class of bug at the architecture level.

**Trade-off accepted:** Higher cognitive overhead during development (async/await 
discipline, explicit `selectinload` instead of implicit lazy loading, no blocking 
calls in request handlers) in exchange for genuine concurrency under load.