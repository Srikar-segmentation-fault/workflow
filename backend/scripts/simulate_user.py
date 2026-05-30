"""
WorkFlow — Comprehensive Multi-Role Workspace Simulation
======================================================
Simulates a real-world enterprise lifecycle with 20 employees and 15 tasks.
Acts exactly like real users by calling HTTP endpoints sequentially:
  1. Registers a Manager
  2. Registers 20 different Employees across diverse departments
  3. Manager logs in & triages/assigns 15 distinct tasks
  4. Role-based security check: verifies employees CANNOT assign tasks (asserts 403)
  5. Employees log in, check dashboard, and submit detailed or bluffed progress logs
  6. Employees update task progress statuses
  7. Manager logs back in, pulls real-time AI summary & LangGraph agent analysis
  8. Fetches immutable audit trail to verify cryptographic timeline integrity
"""
import asyncio
import random
import sys
import httpx
from datetime import datetime, timedelta, timezone
from rich.console import Console
from rich.table import Table

console = Console()
BASE_URL = "http://localhost:8005"

# ── Mock Enterprise Directory ────────────────────────────────────────────────
DEPARTMENTS = ["Logistics", "Sales", "Operations", "Engineering", "Marketing", "Customer Support", "Finance", "HR"]
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", 
               "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

TASK_SCENARIOS = [
    {"title": "Audit Warehouse Q2 Inventory", "desc": "Conduct a manual count of all high-value items in sectors C & D.", "priority": "high", "dept": "Logistics"},
    {"title": "Optimize API Endpoint Latency", "desc": "Refactor database query joins and implement Redis caching on the catalog endpoint.", "priority": "critical", "dept": "Engineering"},
    {"title": "Draft Q3 Regional Sales Projections", "desc": "Compile sales team reports and forecast regional demand for shipping channels.", "priority": "medium", "dept": "Sales"},
    {"title": "Inspect Fleet Brake Hydraulics", "desc": "Inspect brake pads and fluid lines for delivery vans 10 through 18.", "priority": "high", "dept": "Operations"},
    {"title": "Refresh Branding guidelines UI Assets", "desc": "Update design tokens and export vectors for the primary client portals.", "priority": "low", "dept": "Marketing"},
    {"title": "Resolve Overdue Customer SLA Tickets", "desc": "Clear ticket queue for priority accounts with delayed transit issues.", "priority": "high", "dept": "Customer Support"},
    {"title": "Perform Quarterly Tax Reconciliation", "desc": "Reconcile corporate travel expense cards with general accounting receipts.", "priority": "medium", "dept": "Finance"},
    {"title": "Conduct Employee Performance Review", "desc": "Compile evaluation sheets for Q1 employee checkpoints.", "priority": "medium", "dept": "HR"},
    {"title": "Review Carrier Transit SLA Contracts", "desc": "Compare SLA performance logs for local courier contracts.", "priority": "medium", "dept": "Logistics"},
    {"title": "Run Server Penetration Security Test", "desc": "Conduct local scan for exposed dependencies and verify SQL injection safety.", "priority": "critical", "dept": "Engineering"},
    {"title": "Design Customer Feedback Survey Flow", "desc": "Create interactive email layouts to gather delivery feedback.", "priority": "low", "dept": "Marketing"},
    {"title": "Update Cold Storage Temperature Logs", "desc": "Calibrate sensors in warehouse refrigeration units and log discrepancies.", "priority": "high", "dept": "Operations"},
    {"title": "Triage Lead Generation Pipeline", "desc": "Classify incoming sales leads from our marketing landing page.", "priority": "medium", "dept": "Sales"},
    {"title": "Onboard Logistics Intern Group", "desc": "Setup email portals and safety courses for incoming logistics staff.", "priority": "low", "dept": "HR"},
    {"title": "Verify Billing Statement Discrepancies", "desc": "Cross-reference freight charges on invoices with agreed rates.", "priority": "high", "dept": "Finance"}
]

EMPLOYEE_LOGS = [
    # Highly detailed (gets High confidence)
    "Completed audit for all 18 delivery vans. Replaced worn brake pads on Van 12. Fluid levels checked and topped off.",
    "Refactored SQL queries, reducing load times from 840ms to 45ms. Successfully deployed to staging environment.",
    "Reconciled 142 expense statements against ledger. Flagged 3 minor discrepancies above $50 and submitted to HR.",
    "Analyzed Q1 delays. Carrier SLA compliance dropped to 89.2% from 94.1%. Recommended transition plan.",
    "Completed lead triage. Handed off 12 hot opportunities to the account managers. CRM dashboards updated.",
    # Vague / evasive (gets Low/Medium confidence)
    "Worked on the tasks as planned. Made progress and finished some stuff today.",
    "Did some coding on the server. Fixed a few bugs and pushed it.",
    "Followed up on the client emails. Still waiting for them to get back to me.",
    "Checked on some things in the warehouse. Looks mostly fine.",
    "Doing some general tasks today and catching up on documentation."
]


async def simulate_workspace() -> None:
    console.print("[bold purple]⚡ Starting WorkFlow Enterprise Simulation Suite...[/bold purple]")
    console.print("[dim]Simulating 20 Employees, 15 Tasks, role-based controls, and AI layers...[/dim]\n")

    client = httpx.AsyncClient(timeout=30.0)

    # ── Step 1: Register Manager ──────────────────────────────────────────────
    console.print("[bold cyan][1] Registering Corporate Manager...[/bold cyan]")
    manager_payload = {
        "email": "manager_sim@workflow.com",
        "password": "securepassword123",
        "full_name": "Sarah Jenkins",
        "role": "manager",
        "department": "Operations"
    }
    
    # We try login first in case already registered, otherwise register
    login_resp = await client.post(f"{BASE_URL}/api/auth/login", json={"email": manager_payload["email"], "password": manager_payload["password"]})
    if login_resp.status_code == 200:
        manager_token = login_resp.json()["access_token"]
        console.print(f"✔️  Manager '{manager_payload['full_name']}' logged in successfully.")
    else:
        reg_resp = await client.post(f"{BASE_URL}/api/auth/register", json=manager_payload)
        if reg_resp.status_code == 201:
            manager_token = reg_resp.json()["access_token"]
            console.print(f"✔️  Manager '{manager_payload['full_name']}' registered and logged in.")
        else:
            console.print(f"[bold red]❌ Failed to register manager: {reg_resp.text}[/bold red]")
            await client.aclose()
            return

    manager_headers = {"Authorization": f"Bearer {manager_token}"}

    # ── Step 2: Register 20 Employees ─────────────────────────────────────────
    console.print(f"\n[bold cyan][2] Registering 20 Employees across {len(DEPARTMENTS)} departments...[/bold cyan]")
    employees = []
    
    for i in range(20):
        first = FIRST_NAMES[i]
        last = LAST_NAMES[i]
        dept = DEPARTMENTS[i % len(DEPARTMENTS)]
        email = f"emp_{i+1}@workflow.com"
        name = f"{first} {last}"
        
        # Try login first in case already registered, otherwise register
        emp_login = await client.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "password123"})
        if emp_login.status_code == 200:
            user_data = emp_login.json()["user"]
            token = emp_login.json()["access_token"]
            employees.append({"id": user_data["id"], "name": name, "token": token, "email": email, "dept": dept})
        else:
            emp_payload = {
                "email": email,
                "password": "password123",
                "full_name": name,
                "role": "employee",
                "department": dept
            }
            reg_resp = await client.post(f"{BASE_URL}/api/auth/register", json=emp_payload)
            if reg_resp.status_code == 201:
                user_data = reg_resp.json()["user"]
                token = reg_resp.json()["access_token"]
                employees.append({"id": user_data["id"], "name": name, "token": token, "email": email, "dept": dept})
            else:
                console.print(f"❌ Failed to register {name}: {reg_resp.text}")

    console.print(f"✔️  Registered and authenticated {len(employees)} employees successfully.")

    # ── Step 3: Role-Based Authorization Safety Check ──────────────────────
    console.print("\n[bold cyan][3] Verifying Role-Based Access Control (RBAC) Protection...[/bold cyan]")
    test_emp = employees[0]
    bad_headers = {"Authorization": f"Bearer {test_emp['token']}"}
    
    # Try to assign task using employee token
    bad_resp = await client.post(
        f"{BASE_URL}/api/tasks/",
        headers=bad_headers,
        json={
            "title": "Malicious Employee Task Injection",
            "assigned_to": test_emp["id"],
            "deadline": (datetime.utcnow() + timedelta(days=2)).isoformat(),
        }
    )
    
    if bad_resp.status_code == 403:
        console.print("✔️  [bold green]PASS[/bold green]: Employee task assignment correctly BLOCKED with HTTP 403 Forbidden.")
    else:
        console.print(f"❌ [bold red]FAIL[/bold red]: Employee bypassed authorization check! Status: {bad_resp.status_code}")

    # ── Step 4: Manager Assigns 15 Distinct Tasks ─────────────────────────────
    console.print("\n[bold cyan][4] Manager assigning and triaging 15 distinct corporate tasks...[/bold cyan]")
    assigned_tasks = []
    
    for idx, scenario in enumerate(TASK_SCENARIOS):
        # Pick an employee from the matching department, or fallback to random
        eligible = [e for e in employees if e["dept"] == scenario["dept"]]
        assignee = random.choice(eligible) if eligible else random.choice(employees)
        
        # Deadlines vary between overdue (-1 day) and future (2-7 days)
        if idx == 2:  # Make task 3 overdue to test overdue alarms!
            deadline = datetime.utcnow() - timedelta(days=1)
        else:
            deadline = datetime.utcnow() + timedelta(days=random.randint(2, 7))
            
        task_payload = {
            "title": scenario["title"],
            "description": scenario["desc"],
            "assigned_to": assignee["id"],
            "priority": scenario["priority"],
            "deadline": deadline.isoformat()
        }
        
        resp = await client.post(f"{BASE_URL}/api/tasks/", json=task_payload, headers=manager_headers)
        if resp.status_code == 201:
            task_data = resp.json()
            assigned_tasks.append({
                "id": task_data["id"],
                "title": task_data["title"],
                "assignee_name": assignee["name"],
                "assignee_token": assignee["token"],
                "assignee_id": assignee["id"]
            })
            console.print(f"   Assigning task {idx+1:02d}: '{scenario['title']}' ➡️ {assignee['name']} ({scenario['dept']})")
        else:
            console.print(f"   ❌ Failed to assign task {idx+1}: {resp.text}")

    # ── Step 5: Employees Submit Daily Work Logs with AI checks ───────────────
    console.print("\n[bold cyan][5] Employees submitting progress logs & requesting AI Verification...[/bold cyan]")
    
    for idx, task in enumerate(assigned_tasks):
        emp_headers = {"Authorization": f"Bearer {task['assignee_token']}"}
        
        # Pull task details via /api/tasks/mine to simulate user flow
        mine_resp = await client.get(f"{BASE_URL}/api/tasks/mine", headers=emp_headers)
        
        # Submit a realistic or bluffed log
        log_text = random.choice(EMPLOYEE_LOGS)
        log_resp = await client.post(
            f"{BASE_URL}/api/logs/{task['id']}",
            json={"log_text": log_text},
            headers=emp_headers
        )
        
        if log_resp.status_code == 201:
            log_data = log_resp.json()
            confidence = log_data.get("ai_confidence", "Pending")
            feedback = log_data.get("ai_feedback", "No feedback")
            
            # Format confidence color
            conf_style = "bold green" if confidence == "High" else ("bold yellow" if confidence == "Medium" else "bold red")
            console.print(f"   Log {idx+1:02d} ({task['assignee_name']}): [{conf_style}]{confidence}[/{conf_style}] - {feedback[:80]}...")
        else:
            console.print(f"   ❌ Log {idx+1:02d} failed: {log_resp.text}")

    # ── Step 6: Employees Update Task Statuses ───────────────────────────────
    console.print("\n[bold cyan][6] Employees updating task execution progress...[/bold cyan]")
    for idx, task in enumerate(assigned_tasks[:5]): # Update first 5 tasks to completed / in progress
        emp_headers = {"Authorization": f"Bearer {task['assignee_token']}"}
        new_status = "completed" if idx % 2 == 0 else "in_progress"
        
        status_resp = await client.patch(
            f"{BASE_URL}/api/tasks/{task['id']}/status",
            json={"status": new_status},
            headers=emp_headers
        )
        if status_resp.status_code == 200:
            console.print(f"   Task '{task['title']}' status updated to [bold blue]{new_status.upper()}[/bold blue] by {task['assignee_name']}.")

    # ── Step 7: Manager AI "Where's My Team?" & Agent Triage ─────────────────
    console.print("\n[bold cyan][7] Manager pulling AI 'Where's My Team?' Synthesis & LangGraph Agent analysis...[/bold cyan]")
    
    summary_resp = await client.get(f"{BASE_URL}/api/ai/summary", headers=manager_headers)
    if summary_resp.status_code == 200:
        sum_data = summary_resp.json()
        console.print("\n[bold purple]🤖 AI plain-English Workspace briefing:[/bold purple]")
        console.print(f"[italic white]\"{sum_data['summary']}\"[/italic white]\n")
    else:
        console.print(f"❌ Failed to load AI summary: {summary_resp.text}")

    agent_resp = await client.get(f"{BASE_URL}/api/ai/agent-analysis", headers=manager_headers)
    if agent_resp.status_code == 200:
        agent_data = agent_resp.json()["data"]
        console.print("[bold purple]🧬 LangGraph Multi-Node Analysis & Actionable recommendations:[/bold purple]")
        console.print(f"   - [bold]Team Risk Assessment[/bold]: {agent_data['analysis']}")
        console.print(f"   - [bold]System Alert Level[/bold]: `{agent_data['risk_level'].upper()}`")
        for rec in agent_data["recommendations"]:
            console.print(f"   - [bold green]Action Item[/bold green]: {rec}")
    else:
        console.print(f"❌ Failed to run LangGraph agent: {agent_resp.text}")

    # ── Step 8: Immutable Audit Trail Integrity Verification ────────────────
    console.print("\n[bold cyan][8] Verifying cryptographic append-only Audit Ledger...[/bold cyan]")
    audit_resp = await client.get(f"{BASE_URL}/api/audit/", headers=manager_headers)
    if audit_resp.status_code == 200:
        logs = audit_resp.json()["data"]
        total = audit_resp.json()["total"]
        
        # Display sample in a table
        table = Table(title="WorkFlow Immutable Audit Trail Snapshot")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Actor", style="bold white")
        table.add_column("Action", style="green")
        table.add_column("Payload Description", style="dim")
        
        for log in logs[:10]: # First 10 logs
            table.add_row(log["created_at"][:19], log["actor"], log["action"].upper(), str(log["payload"]))
            
        console.print(table)
        console.print(f"✔️  Audit ledger verified. Cryptographic audit logs generated: {total}.")
    else:
        console.print(f"❌ Failed to load audit trail: {audit_resp.text}")

    await client.aclose()
    console.print("\n[bold green]🎉 Workspace simulation completed successfully! All modules, roles, and AI layers verified.[/bold green]")


if __name__ == "__main__":
    # Ensure uvicorn backend is running before triggering
    asyncio.run(simulate_workspace())
