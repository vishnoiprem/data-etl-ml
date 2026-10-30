# =============================================================================
# Makro LLM Gateway — Client
# File: client.py
# How to use: python client.py
#
# This is how OTHER services call your LangServe API:
#   - Power BI reports
#   - Internal dashboards
#   - Databricks notebooks
#   - Other Python microservices
# =============================================================================

import httpx
from langserve import RemoteRunnable

BASE_URL = "http://localhost:8000"   # change to your Azure container URL in prod

# =============================================================================
# CLIENT 1 — Simple LLM chain
# =============================================================================

# Option A — LangServe RemoteRunnable (recommended)
# Behaves exactly like a local chain — .invoke(), .stream(), .batch()
llm_chain = RemoteRunnable(f"{BASE_URL}/llm-chain")

# Single invoke
response = llm_chain.invoke({"input": "What is the top selling category in Makro Thailand?"})
print("Response:", response)

# Streaming — tokens arrive one by one
print("\nStreaming response:")
for chunk in llm_chain.stream({"input": "Explain O2O sales strategy for Makro"}):
    print(chunk, end="", flush=True)

# Batch — multiple inputs in one call (efficient)
responses = llm_chain.batch([
    {"input": "Summarise Q1 2024 sales trend"},
    {"input": "What is CPAxtra Axtra360?"},
    {"input": "Explain SSBI in simple terms"},
])
for r in responses:
    print("\n-", r[:100])

# Option B — plain HTTP (for non-Python callers)
response = httpx.post(
    f"{BASE_URL}/llm-chain/invoke",
    json={"input": {"input": "What is Makro's main customer segment?"}},
    timeout=30
)
print("\nHTTP response:", response.json()["output"])

# =============================================================================
# CLIENT 2 — Multi-user conversational chatbot
# Each user passes their own session_id — full isolated conversation history
# =============================================================================

chatbot = RemoteRunnable(f"{BASE_URL}/chatbot")

# ── User 1: Store manager in Bangkok ────────────────────────────────────────
config_user1 = {"configurable": {"session_id": "store_mgr_bkk_001"}}

# Turn 1
r1 = chatbot.invoke(
    {"input": "สวัสดี วันนี้ยอดขายสาขาบางนาเป็นอย่างไรบ้าง?"},
    config=config_user1
)
print("\nUser1 Turn1:", r1)

# Turn 2 — BERT remembers context from Turn 1
r2 = chatbot.invoke(
    {"input": "แล้วเปรียบเทียบกับสัปดาห์ที่แล้วล่ะ?"},   # "compare with last week?"
    config=config_user1
)
print("User1 Turn2:", r2)

# ── User 2: Supplier manager at Nestle ──────────────────────────────────────
config_user2 = {"configurable": {"session_id": "supplier_nestle_th"}}

r3 = chatbot.invoke(
    {"input": "What is the current stock level for Nestle products in central warehouse?"},
    config=config_user2
)
print("\nUser2 Turn1:", r3)

# User 1 and User 2 have completely separate histories
# user1 asking follow-up doesn't affect user2's context — ever

# =============================================================================
# CLIENT 3 — Async client (for production services handling many requests)
# =============================================================================

import asyncio

async def async_example():
    chatbot_async = RemoteRunnable(f"{BASE_URL}/chatbot")

    # Both users served concurrently — no blocking
    results = await asyncio.gather(
        chatbot_async.ainvoke(
            {"input": "Show me fraud alerts for today"},
            config={"configurable": {"session_id": "fraud_analyst_01"}}
        ),
        chatbot_async.ainvoke(
            {"input": "What promotions are running this week?"},
            config={"configurable": {"session_id": "marketing_user_02"}}
        ),
    )
    for r in results:
        print("Async result:", r[:80])

asyncio.run(async_example())
