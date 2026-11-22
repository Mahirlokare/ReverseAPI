# Reverse API Engineer

A full-stack SaaS application for API discovery, reverse engineering, and client generation. Built with React + Vite frontend, FastAPI backend, PostgreSQL, Redis, and Supabase.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend       │────▶│   Database      │
│   (React+Vite)  │     │   (FastAPI)     │     │   (PostgreSQL)  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
             ┌─────────────┐           ┌─────────────┐
             │   Redis     │           │  Celery     │
             │  (Cache/    │           │  Workers    │
             │   Queue)    │           │  (CLI Exec) │
             └─────────────┘           └─────────────┘
                    ▲                         │
                    │                         ▼
             ┌─────────────┐           ┌─────────────┐
             │  Supabase   │           │  Playwright │
             │ (Auth/Store)│           │ (Browser)   │
             └─────────────┘           └─────────────┘
```

## Features

- **Project Management**: Create and organize API discovery projects
- **Guided Discovery Workflow**: Step-by-step form for target URL, task description, and configuration
- **Multiple Execution Modes**: Agent (AI-driven), Manual (user-driven), Engineer (re-generate from captures)
- **Live Execution Monitoring**: Real-time status updates via WebSocket
- **API Endpoint Explorer**: Browse, search, and inspect discovered endpoints
- **Request/Response Inspector**: Detailed view with syntax highlighting
- **HAR Capture Management**: Import, export, and manage network captures
- **Generated Client Management**: View, download, and execute generated API clients
- **AI Provider Configuration**: Manage multiple AI providers and models
- **Browser Provider Management**: Configure Playwright, Chrome MCP, etc.
- **Authentication**: JWT-based auth with Supabase integration
- **Responsive UI**: Works on desktop, tablet, and mobile

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite 5
- Tailwind CSS
- shadcn/ui components
- TanStack Query (React Query)
- React Router 6
- Zustand (state management)
- Axios (HTTP client)
- Lucide Icons

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL (asyncpg)
- Redis
- Celery (background tasks)
- Pydantic 2
- JWT Authentication
- Structlog (logging)

### Infrastructure
- Docker & Docker Compose
- PostgreSQL 16
- Redis 7
- Playwright (browser automation)

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)
- Supabase account (for auth/storage)

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
cd ReverseAPIEngineer
```

2. Copy environment file:
```bash
cp .env.example .env
# Edit .env with your values
```

3. Start all services:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .[dev]
cp ../.env.example .env
# Edit .env
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

#### Celery Worker
```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

## Environment Variables

See `.env.example` for all configuration options. Key variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `SECRET_KEY` | JWT signing secret (min 32 chars) |
| `CLI_EXECUTABLE_PATH` | Path to reverse-api-engineer CLI |
| `ANTHROPIC_API_KEY` | Anthropic API key for AI features |

## Project Structure

```
ReverseAPIEngineer/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # API routes
│   │   ├── core/             # Config, security, database
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic (CLI service)
│   │   ├── workers/          # Celery tasks
│   │   └── main.py           # FastAPI app
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── lib/              # Utilities, API client, auth
│   │   ├── hooks/            # Custom hooks
│   │   ├── types/            # TypeScript types
│   │   └── styles/           # Global styles
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user

### Projects
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Discovery Runs
- `GET /api/v1/runs` - List runs
- `POST /api/v1/runs` - Create run (starts discovery)
- `GET /api/v1/runs/{id}` - Get run details
- `POST /api/v1/runs/{id}/cancel` - Cancel run
- `POST /api/v1/runs/{id}/retry` - Retry failed run
- `GET /api/v1/runs/{id}/events` - Get run events
- `GET /api/v1/runs/{id}/logs` - Get run logs

### Endpoints
- `GET /api/v1/endpoints` - List endpoints
- `GET /api/v1/endpoints/{id}` - Get endpoint details

### Captures
- `GET /api/v1/captures` - List captures
- `GET /api/v1/captures/{id}` - Get capture details

### Clients
- `GET /api/v1/clients` - List generated clients
- `GET /api/v1/clients/{id}` - Get client details

### AI Providers
- `GET /api/v1/ai-providers` - List providers
- `POST /api/v1/ai-providers` - Add provider
- `PUT /api/v1/ai-providers/{id}` - Update provider

### Settings
- `GET /api/v1/settings/preferences` - Get user preferences
- `PUT /api/v1/settings/preferences` - Update preferences

## Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Linting
```bash
# Backend
cd backend
ruff check .
mypy .

# Frontend
cd frontend
npm run lint
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Deployment

### Production Considerations

1. **Security**:
   - Use strong `SECRET_KEY`
   - Enable HTTPS
   - Configure proper CORS origins
   - Use Supabase service role key only on backend

2. **Scaling**:
   - Run multiple Celery workers
   - Use Redis Cluster for high availability
   - Use PostgreSQL read replicas
   - Configure load balancer for frontend

3. **Monitoring**:
   - Add Sentry for error tracking
   - Configure structured logging
   - Set up health checks

4. **Storage**:
   - Use S3-compatible storage for artifacts
   - Configure CDN for frontend assets

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

For issues and feature requests, please use the GitHub issue tracker.