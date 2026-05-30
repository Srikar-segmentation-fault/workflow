"""
Ollama / qwen2.5 live verification script.
Run: .venv\Scripts\python.exe test_ollama.py

Prints raw LLM responses to console so you can confirm
the model is returning real generated text.
"""
import asyncio
import json
import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv(".env")

BASE_URL  = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL     = os.getenv("OLLAMA_MODEL", "qwen2.5")

print(f"\n{'='*60}")
print(f"  Provider : Ollama (local)")
print(f"  Model    : {MODEL}")
print(f"  Base URL : {BASE_URL}")
print(f"{'='*60}\n")


async def chat(system: str, user: str, json_mode: bool = False) -> str:
    if json_mode:
        user += "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no extra text."
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 300},
    }
    if json_mode:
        payload["format"] = "json"

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{BASE_URL}/api/chat", json=payload)
        resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


async def test_basic():
    print("TEST 1 — Basic call")
    print("-" * 40)
    result = await chat(
        system="You are a helpful assistant.",
        user="Say exactly: 'qwen2.5 via Ollama is live.' then state what model you are.",
    )
    print(f"  LLM response: {result}")
    print()


async def test_log_verification():
    print("TEST 2 — Work-log verification (JSON mode)")
    print("-" * 40)
    result = await chat(
        system=(
            "You are a workplace accountability assistant. Evaluate whether an "
            "employee's daily work log genuinely reflects real progress on their task."
        ),
        user="""\
Task title: Prepare Q2 Sales Report
Task description: Compile all Q2 sales figures and create a summary deck.

Employee's work log:
I pulled the raw sales data from the CRM and started building the slide deck.
Completed slides 1-5 covering revenue breakdown by region. Still need to add
the YoY comparison charts and the executive summary.

Evaluate this log. Respond ONLY with valid JSON:
{"confidence": "High" | "Medium" | "Low", "feedback": "one sentence explanation"}""",
        json_mode=True,
    )
    print(f"  Raw JSON from model:\n  {result}")
    try:
        clean = re.sub(r"```(?:json)?|```", "", result).strip()
        data = json.loads(clean)
        print(f"\n  Parsed confidence : {data.get('confidence')}")
        print(f"  Parsed feedback   : {data.get('feedback')}")
    except Exception as e:
        print(f"  (JSON parse note: {e})")
    print()


async def test_manager_summary():
    print("TEST 3 — Manager team summary")
    print("-" * 40)
    result = await chat(
        system=(
            "You are a productivity assistant helping a manager understand "
            "their team's work status. Be concise and highlight risks."
        ),
        user="""\
Here is the current task list:
• Prepare Q2 Sales Report | Bob Employee | HIGH | deadline 2026-05-28 (-2d) | in_progress
• Update Client Onboarding Docs | Carol Smith | MEDIUM | deadline 2026-06-02 (+3d) | pending
• Fix Invoice Discrepancy | David Lee | HIGH | deadline 2026-05-29 (-1d) | pending

Write a short plain-English briefing (max 4 sentences) covering who is behind,
what is at risk, and who is on track.""",
    )
    print(f"  LLM summary:\n{result}")
    print()


async def main():
    # First check Ollama is reachable
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BASE_URL}/api/tags")
            models = [m["name"] for m in resp.json().get("models", [])]
            print(f"  Ollama running. Available models: {models}")
            if not any(MODEL in m for m in models):
                print(f"\n  WARNING: '{MODEL}' not found. Run: ollama pull {MODEL}")
                print(f"  Attempting anyway...\n")
            else:
                print(f"  '{MODEL}' is ready.\n")
    except Exception as e:
        print(f"  ERROR: Cannot reach Ollama at {BASE_URL}")
        print(f"  Make sure Ollama is running: ollama serve")
        print(f"  Details: {e}")
        return

    try:
        await test_basic()
        await test_log_verification()
        await test_manager_summary()
        print("=" * 60)
        print("  ALL TESTS PASSED — qwen2.5 is live via Ollama.")
        print("=" * 60)
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")


asyncio.run(main())
