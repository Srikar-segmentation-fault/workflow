# WorkFlow — AI-Powered, Role-Based Employee Task & Accountability Platform

**An Enterprise Productivity and AI Accountability Platform replacing messy spreadsheets and verbal agreements with a verifiable, tamper-resistant system.**

---

## 📌 Problem Statement
Most small and mid-sized businesses manage employee tasks using scattered spreadsheets, chat threads, or verbal instructions. This leads to a critical breakdown in workplace accountability, zero verification of completed work, and significant time wasted (up to 30-40%) by managers manually chasing updates. Overperforming workers go unrecognized while underperformers slip under the radar.

---

## ⚡ The Solution — WorkFlow
WorkFlow replaces this fragmentation with a single source of truth:
* **Role-Based Task Control:** Managers assign deliverables with clear due dates; employees receive unambiguous priorities.
* **Tamper-Resistant Audit Trail:** Every single state change, update, and submission is recorded in an immutable, append-only ledger.
* **Accountability-First logs:** Employees submit concrete daily progress statements instead of simple checkboxes.
* **AI Credibility Verification:** A local LLM scans employee statements in real-time, verifying credibility against the assignment and flagging bluffing automatically.

---

## 🧠 AI-Powered Features

1. **AI Work-Log Verification:** Analyzes employee log statements to check if they match the assigned task, flagging vague, low-effort, or bluffed progress with a real-time Confidence Signal (`High` | `Medium` | `Low`).
2. **"Where's My Team?" Manager briefing:** Automatically turns the entire task matrix into a plain-English briefing in 5 concise sentences, highlighting overdue deliverables, slipping milestones, and outstanding employees.
3. **Smart Task Triage:** Automatically suggests realistic deadlines and priority ratings based on the task description.
4. **LangGraph Accountability Agent:** A multi-step reasoning agent routing task matrices through risk analysis nodes, flagging employee patterns, and outputting actionable productivity recommendations.
5. **RAG Semantic Task History Search:** Uses LlamaIndex and PostgreSQL `pgvector` to index all logs, allowing managers to execute semantic queries across past tasks.

---

## 🛠️ Technology Stack
* **Backend:** FastAPI (Python 3.12+), SQLModel (SQLAlchemy + Pydantic v2), asyncpg
* **Frontend:** Streamlit 1.40+ (Glassmorphism Dark Theme, styled micro-interactions)
* **Database:** Supabase PostgreSQL (Row-Level Security, vector index support)
* **AI Orchestration:** LangChain 0.3, LangGraph (Agent State Workflows)
* **LlamaIndex RAG:** VectorStoreIndex, pgvector semantic indexing
* **LLM Engine:** Local Ollama (`llama3.2:3b` / `nomic-embed-text`)
* **Environment:** `uv` (Fast package manager), Docker Compose (Postgres/Ollama)

---

## 🚀 Setup & Installation

### 1. Start Infrastructure
Run the database and Ollama using Docker Compose:
```bash
docker-compose up -d
```

### 2. Configure Environment
Create a `.env` file in the `backend/` directory from the example:
```bash
cp backend/.env.example backend/.env
```
Ensure you update the Supabase URLs if using cloud Supabase, or keep the defaults if connecting to local docker PostgreSQL.

### 3. Install Python Dependencies
Using `uv`, synchronize packages and build the environment instantly:
```bash
cd backend
uv sync
```

### 4. Pull Local AI Models
If running Ollama locally:
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 5. Seed Demo Workspaces
Create the demo manager, employees, sample tasks, and historical work logs:
```bash
uv run python scripts/seed.py
```

### 6. Run the Servers
Start the FastAPI backend:
```bash
uv run uvicorn app.main:app --reload --port 8000
```

Start the Streamlit frontend:
```bash
cd ../frontend
uv run streamlit run app.py
```

---

## 🎯 Demo Walkthrough

1. **Step 1: Secure Authentication**
   * Navigate to `http://localhost:8501`.
   * Log in as a **Manager**: Email `manager@demo.com`, Password `password123`.

2. **Step 2: Assign an AI-Triaged Task**
   * Go to **Assign New Task**.
   * Enter a title: `"Reconcile Logistics transit logs for warehouse B"`.
   * Click **Request AI Smart Triage** to let Ollama automatically determine priority and suggest a deadline with reasoning.
   * Click **Confirm and Assign** to assign it to Bob.

3. **Step 3: Employee Progress Update**
   * Log out, and log back in as an **Employee**: Email `employee1@demo.com`, Password `password123`.
   * Go to **Submit Work Log**.
   * Try entering a bluff entry: `"working on it, finishing soon."` -> submit and see the AI flag it with **LOW confidence**.
   * Now enter a detailed, factual entry: `"Completed reconciliation for all 42 shipments. Found 2 transit time discrepancies and logged them."` -> see the AI reward it with **HIGH confidence**.

4. **Step 4: Real-time Team Briefing**
   * Log back in as a **Manager** (`manager@demo.com`).
   * Navigate to **'Where's My Team?' AI Summary**.
   * Click **Generate Real-time AI Summary** and read a plain-English synthesis of who is behind and who is overperforming.
   * Click **Run Accountability Agent** to trigger the LangGraph flow and view custom strategic recommendations.
   * Navigate to the **Immutable Audit Trail** to view the cryptographically timeline logs of every event.
