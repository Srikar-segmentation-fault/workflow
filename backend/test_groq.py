"""
Quick Groq verification script.
Run: .venv\Scripts\python.exe test_groq.py
Prints the raw LLM response to console so you can confirm it's live.
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv(".env")

GROQ_KEY = os.getenv("GROQ_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

print(f"\n{'='*60}")
print(f"  Groq Key   : {GROQ_KEY[:12]}...{GROQ_KEY[-4:]} (masked)")
print(f"  Model      : {GROQ_MODEL}")
print(f"{'='*60}\n")


async def test_basic_call():
    """Test 1 — plain chat call."""
    from groq import AsyncGroq
    client = AsyncGroq(api_key=GROQ_KEY)

    print("TEST 1: Basic chat call")
    print("-" * 40)
    response = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user",   "content": "Say exactly: 'Groq is live and responding.' then add today's date in ISO format."},
        ],
        temperature=0.0,
        max_tokens=60,
    )
    content = response.choices[0].message.content
    print(f"  LLM response : {content}")
    print(f"  Model used   : {response.model}")
    print(f"  Tokens used  : {response.usage.total_tokens}")
    print()


async def test_log_verification():
    """Test 2 — simulate a real work-log verification call."""
    from groq import AsyncGroq
    client = AsyncGroq(api_key=GROQ_KEY)

    print("TEST 2: Work-log verification (JSON mode)")
    print("-" * 40)

    system = (
        "You are a workplace accountability assistant. Evaluate whether an "
        "employee's daily work log genuinely reflects real progress on their task."
    )
    user = """\
Task title: Prepare Q2 Sales Report
Task description: Compile all Q2 sales figures and create a summary deck.

Employee's work log:
I pulled the raw sales data from the CRM and started building the slide deck. 
Completed slides 1-5 covering revenue breakdown by region. Still need to add 
the YoY comparison charts and the executive summary.

No proof file was attached.

Evaluate this log. Respond ONLY with valid JSON:
{"confidence": "High" | "Medium" | "Low", "feedback": "one sentence explanation"}"""

    response = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.0,
        max_tokens=150,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    print(f"  Raw JSON from LLM : {content}")
    print(f"  Model used        : {response.model}")
    print(f"  Tokens used       : {response.usage.total_tokens}")
    print()


async def test_manager_summary():
    """Test 3 — simulate the manager summary call."""
    from groq import AsyncGroq
    client = AsyncGroq(api_key=GROQ_KEY)

    print("TEST 3: Manager summary")
    print("-" * 40)

    task_table = """\
• Prepare Q2 Sales Report | Bob Employee | HIGH priority | deadline 2026-05-28 (-2d) | in_progress
• Update Client Onboarding Docs | Carol Smith | MEDIUM priority | deadline 2026-06-02 (+3d) | pending
• Fix Invoice Discrepancy | David Lee | HIGH priority | deadline 2026-05-29 (-1d) | pending"""

    response = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a productivity assistant helping a manager understand their team's work status. Be concise and highlight risks.",
            },
            {
                "role": "user",
                "content": f"Here is the current task list:\n{task_table}\n\nWrite a short plain-English briefing (max 4 sentences) covering who is behind, what is at risk, and who is on track.",
            },
        ],
        temperature=0.3,
        max_tokens=200,
    )
    content = response.choices[0].message.content
    print(f"  LLM summary:\n{content}")
    print(f"\n  Model used  : {response.model}")
    print(f"  Tokens used : {response.usage.total_tokens}")
    print()


async def main():
    if not GROQ_KEY or GROQ_KEY == "":
        print("ERROR: GROQ_KEY is empty in .env — cannot run tests.")
        return

    try:
        await test_basic_call()
        await test_log_verification()
        await test_manager_summary()
        print("=" * 60)
        print("  ALL TESTS PASSED — Groq is live and returning real LLM output.")
        print("=" * 60)
    except Exception as e:
        print(f"\nERROR: {e}")
        print("Check your GROQ_KEY and internet connection.")


asyncio.run(main())
