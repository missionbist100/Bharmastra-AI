# Bharmastra-AI

Bharmastra-AI is an AI-powered coding and research assistant designed for developers, students, startups, and enterprises. It provides deep research, project planning, automated backend generation, code review, bug detection, and conversational software development workflows — packaged as a modular, production-ready foundation.

Key goals:
- Help teams and individuals rapidly prototype and build backend systems.
- Provide research and planning workflows that increase developer productivity.
- Offer an extensible OpenAI-compatible model integration layer to support multiple providers.

## Features

- Research assistant: structured research requests, comparisons, and analysis.
- Project planning: generate project plans, feature lists, and architecture diagrams.
- Backend generation: scaffold backend services, APIs, and database schemas.
- Code review: automated review, bug detection, and optimization suggestions.
- Conversational workflows: context-aware chat and project continuation.
- Provider-agnostic AI layer: supports OpenAI, Anthropic, Google Gemini, and local Ollama providers.
- Production-ready foundation: FastAPI, PostgreSQL, SQLAlchemy, Pydantic, Docker, and GitHub Actions CI.

## Quick Start

Prerequisites:
- Python 3.12
- Docker & docker-compose
- PostgreSQL (or use docker-compose provided)
- An OpenAI-compatible API key (or other provider credentials)

1. Clone the repo:

```bash
git clone https://github.com/missionbist100/Bharmastra-AI.git
cd Bharmastra-AI
```

2. Copy and edit environment variables:

```bash
cp .env.example .env
# Edit .env to add your credentials and configuration
```

3. Start with Docker Compose (development):

```bash
docker compose up --build
```

4. Run migrations (Alembic-ready structure is provided):

```bash
# inside the web container or locally with env set
alembic upgrade head
```

5. Open http://localhost:8000/docs for the interactive API docs (FastAPI / OpenAPI).

## Installation (local development)

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set up environment variables (see `.env.example`).
3. Initialize the database and run migrations.
4. Start the FastAPI application:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Usage Examples

All endpoints are under `/api/v1` and expect JSON requests with authentication using JWT (Authorization: Bearer <token>).

Example: Research endpoint

```bash
curl -X POST http://localhost:8000/api/v1/research \
  -H "Authorization: Bearer $BHARMASTRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "best practices for Python microservices in 2026", "depth": 3}'
```

Example: Generate backend

```bash
curl -X POST http://localhost:8000/api/v1/generate-backend \
  -H "Authorization: Bearer $BHARMASTRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_name":"todo-app","language":"python","database":"postgresql"}'
```

Chat example

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $BHARMASTRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 1, "message": "Help me design the authentication flow"}'
```

## Environment Variables

Key variables in `.env` (see `.env.example`):

- DATABASE_URL=postgresql+asyncpg://user:password@db:5432/bharmastra
- SECRET_KEY=supersecretjwtkey
- ALGORITHM=HS256
- ACCESS_TOKEN_EXPIRE_MINUTES=60
- AI_PROVIDER=openai
- OPENAI_API_KEY=...

## Architecture (Mermaid)

```mermaid
flowchart TB
  subgraph API
    A[FastAPI Endpoints] --> B[Service Layer]
  end
  B --> C[AI Provider Abstraction]
  C --> D[OpenAI / Anthropic / Gemini / Ollama]
  B --> E[Database (Postgres)]
  E --> F[SQLAlchemy / Alembic]
  B --> G[Background Workers (Celery/Kafka - future)]

  style A fill:#f9f,stroke:#333,stroke-width:1px;
  style D fill:#ff9,stroke:#333,stroke-width:1px;
  style E fill:#9ff,stroke:#333,stroke-width:1px;
```

## Development Roadmap (v1 -> v2)

- v1 (MVP): Research, Project Planning, Backend Generation, Code Review, Chat, Multi-provider AI layer, Authentication, DB models, Docker, CI.
- v1.1: Add user roles, usage analytics, billing hooks, rate-limiting per-user, improved tests, deployment scripts.
- v2: Real-time collaboration, code completions in-editor, IDE plugins, advanced RAG (retrieval-augmented generation), knowledge bases.

## Contributing

See CONTRIBUTING.md for development setup, branch naming, testing and PR workflow.

## License

This project is licensed under the MIT License — see LICENSE for details.
