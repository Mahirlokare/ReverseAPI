# Reverse API Engineer

A production-grade full-stack SaaS platform for autonomous API discovery, network traffic reverse engineering, and SDK client generation. Built with a React + Vite TypeScript frontend, FastAPI async backend, SQLite / PostgreSQL persistence, and background execution engine.

---

## Architecture Overview

```text
┌─────────────────────────┐          ┌─────────────────────────┐          ┌─────────────────────────┐
│     React + Vite UI     │ ───────▶ │     FastAPI Backend     │ ───────▶ │   SQLite / PostgreSQL   │
│  http://localhost:5173  │          │  http://localhost:8000  │          │    Database Storage     │
└─────────────────────────┘          └────────────┬────────────┘          └─────────────────────────┘
             │                                    │
             │                                    ▼
             │                       ┌─────────────────────────┐
             │                       │  Async Engine & Workers │
             │                       │  (Traffic Capture & SDK)│
             │                       └────────────┬────────────┘
             │                                    │
             ▼                                    ▼
┌─────────────────────────┐          ┌─────────────────────────┐
│   WebSocket Real-time   │ ◀─────── │   Playwright Browser    │
│    Execution Monitor    │          │  (Headless DOM Crawl)   │
└─────────────────────────┘          └─────────────────────────┘
```

---

## Features

- **Guided Discovery Workflow**: Multi-step wizard configuring target URLs, discovery goals, execution modes, and language outputs.
- **Multiple Execution Modes**:
  - `Agent Mode`: AI explores web pages and triggers actions autonomously.
  - `Manual Mode`: Interactively captures live network sessions.
  - `Engineer Mode`: Regenerates clean client SDKs from saved HAR captures.
- **Live 10-Stage Execution Monitor**: Real-time progress updates with event streams and console logs.
- **API Endpoint Catalog**: Search, filter, and inspect discovered REST endpoints with query parameters, headers, and request/response payloads.
- **Client SDK Generator**: Generates clean, type-safe API clients across multiple languages (TypeScript, Python, JavaScript, Go, etc.).
- **HAR Network Captures**: Inspect, download, and replay captured HTTP traffic.
- **JWT Authentication & RBAC**: Secure token refresh with role-based access.

---

## Prerequisites

- **Node.js**: v18+ or v20+ (`node -v`)
- **Python**: 3.11+ (`python --version`)
- **Git** (`git --version`)

---

## Running Commands (Step-by-Step)

### 1. Clone the Repository
```bash
git clone https://github.com/Mahirlokare/ReverseAPI.git
cd ReverseAPI
```

---

### 2. Backend Setup & Run

Open a terminal in the project root:

#### Windows (PowerShell):
```powershell
cd backend

# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .[dev]

# Start FastAPI backend server with auto-reload
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### macOS / Linux (Bash):
```bash
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e .[dev]

# Start FastAPI backend server with auto-reload
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

*Backend server will start at: **http://127.0.0.1:8000***  
*Interactive Swagger API Docs: **http://127.0.0.1:8000/docs***  
*Health Check: **http://127.0.0.1:8000/health***

---

### 3. Frontend Setup & Run

Open a **second terminal** in the project root:

```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```

*Frontend web app will start at: **http://127.0.0.1:5173***

---

### 4. Running via Docker Compose (Optional)

To spin up the entire stack with PostgreSQL and Redis:

```bash
# Copy example environment variables
cp .env.example .env

# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f
```

---

### 5. Running Tests

#### Backend Tests (Pytest):
```powershell
# In backend directory with virtual environment activated:
pytest tests/ -v
```

#### Frontend Build & Type Check:
```bash
# In frontend directory:
npm run build
```

---

### 6. Sharing Demo Link with Friends (Public Tunnel)

To share your local instance publicly without deploying:

```powershell
# Run a secure HTTPS tunnel to your frontend (port 5173):
ssh -o StrictHostKeyChecking=no -T -R 80:127.0.0.1:5173 nokey@localhost.run
```
Copy the generated `https://*.app.lhr.life` link and share it directly. All frontend views and backend API calls (`/api/v1`) are proxied automatically.

---

## Default Endpoints Summary

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend Web App** | `http://localhost:5173` | React Dashboard, Discovery Wizard, Monitoring |
| **Backend API** | `http://localhost:8000` | FastAPI REST API |
| **Swagger UI Docs** | `http://localhost:8000/docs` | Interactive OpenAPI schema & test interface |
| **ReDoc** | `http://localhost:8000/redoc` | Alternative API reference documentation |
| **Health Check** | `http://localhost:8000/health` | Backend and database connectivity status |

---

## Project Structure

```text
ReverseAPIEngineer/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/  # Auth, Projects, Runs, Endpoints, Captures, Clients
│   │   ├── core/              # Config, Security (JWT/bcrypt), Database (SQLAlchemy)
│   │   ├── models/            # Database entity models
│   │   ├── schemas/           # Pydantic v2 validation models
│   │   ├── services/          # CLI & autonomous discovery execution service
│   │   └── main.py            # FastAPI application entry point
│   ├── tests/                 # Async pytest test suite
│   └── pyproject.toml         # Backend dependencies & configuration
├── frontend/
│   ├── src/
│   │   ├── components/        # Layout, ErrorBoundary, UI components
│   │   ├── lib/               # Axios API client, Zustand Auth store
│   │   ├── pages/             # Dashboard, Discovery, Projects, RunMonitor, Settings
│   │   └── App.tsx            # Routes & Protected Route Guards
│   ├── package.json
│   └── vite.config.ts         # Vite server & API proxy configuration
├── docker-compose.yml
└── README.md
```

---

## License

MIT License.
