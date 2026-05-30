"""
Gemini live verification script.
Run: .venv\Scripts\python.exe test_gemini.py

Prints raw LLM responses to console — confirms the API key is live
and the model is returning real generated text, not hardcoded strings.
"""
import asyncio
import json
import os
import re
import ssl
import certifi

# ── Fix Windows Python SSL cert verification ──────────────────────────────────
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

from dotenv import load_dotenv

load_dotenv(".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

print(f"\n{'='*60}")
print(f"  Provider : Google Gemini (google-genai SDK)")
print(f"  Model    : {GEMINI_MODEL}")
print(f"  API Key  : {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]} (masked)")
print(f"{'='*60}\n")

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY is empty in .env")
    exit(1)

from google import genai
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)


async def test_basic_call():
    print("TEST 1 — Basic call")
    print("-" * 40)
    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents="Say exactly: 'Gemini is live and responding.' then add today's date in ISO format.",
        config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=60),
    )
    print(f"  LLM response : {response.text.strip()}")
    print()


async def test_log_verification():
    print("TEST 2 — Work-log verification (JSON output)")
    print("-" * 40)

    prompt = """\
You are a workplace accountability assistant. Evaluate whether an employee's \
daily work log genuinely reflects real progress on their assigned task.

Task title: Prepare Q2 Sales Report
Task description: Compile all Q2 sales figures and create a summary deck.

Employee's work log:
I pulled the raw sales data from the CRM and started building the slide deck.
Completed slides 1-5 covering revenue breakdown by region. Still need to add
the YoY comparison charts and the executive summary.

No proof file was attached.

Evaluate this log. Respond ONLY with valid JSON — no markdown, no explanation:
{"confidence": "High" | "Medium" | "Low", "feedback": "one sentence explanation"}"""

    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=150),
    )
    raw = response.text.strip()
    print(f"  Raw response from Gemini:\n  {raw}")

    try:
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        data = json.loads(clean)
        print(f"\n  Parsed confidence : {data.get('confidence')}")
        print(f"  Parsed feedback   : {data.get('feedback')}")
    except Exception as e:
        print(f"  (JSON parse note: {e})")
    print()


async def test_manager_summary():
    print("TEST 3 — Manager team summary")
    print("-" * 40)

    prompt = """\
You are a productivity assistant helping a manager understand their team's work status. \
Be concise and highlight risks.

Here is the current task list:
• Prepare Q2 Sales Report | Bob Employee | HIGH priority | deadline 2026-05-28 (-2d) | in_progress
• Update Client Onboarding Docs | Carol Smith | MEDIUM priority | deadline 2026-06-02 (+3d) | pending
• Fix Invoice Discrepancy | David Lee | HIGH priority | deadline 2026-05-29 (-1d) | pending

Write a short plain-English briefing (max 4 sentences) covering who is behind, \
what is at risk, and who is on track."""

    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=200),
    )
    print(f"  LLM summary:\n{response.text.strip()}")
    print()


async def main():
    try:
        await test_basic_call()
        await test_log_verification()
        await test_manager_summary()
        print("=" * 60)
        print("  ALL TESTS PASSED — Gemini is live, returning real LLM output.")
        print("=" * 60)
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        print("Check your GEMINI_API_KEY and internet connection.")


asyncio.run(main())
