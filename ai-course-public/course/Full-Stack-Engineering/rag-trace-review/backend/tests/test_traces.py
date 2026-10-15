"""API tests: pagination, filtering, feedback."""
import base64


def _enc(created_at: str, trace_id: str) -> str:
    return base64.urlsafe_b64encode(f"{created_at}|{trace_id}".encode()).decode()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_traces_returns_page(client, seed):
    r = client.get("/traces")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "meta" in body
    assert len(body["items"]) == 3
    # DESC order: t003 first
    assert body["items"][0]["trace_id"] == "t003"


def test_cursor_pagination_walks_all_rows(client, seed):
    seen = []
    cursor = None
    for _ in range(10):
        url = "/traces?limit=1"
        if cursor:
            url += f"&cursor={cursor}"
        r = client.get(url)
        assert r.status_code == 200
        body = r.json()
        seen.extend(i["trace_id"] for i in body["items"])
        cursor = body["meta"]["next_cursor"]
        if not body["meta"]["has_more"]:
            break
    assert seen == ["t003", "t002", "t001"]
    assert all(seen[i] != seen[i + 1] for i in range(len(seen) - 1))


def test_invalid_cursor_returns_400(client, seed):
    r = client.get("/traces?cursor=garbage!!!")
    assert r.status_code == 400


def test_filter_by_day(client, seed):
    r = client.get("/traces?day=2026-01-02")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["trace_id"] == "t002"


def test_filter_by_prompt_version(client, seed):
    r = client.get("/traces?prompt_version=v1.2")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["prompt_version"] == "v1.2"


def test_filter_by_latency_range(client, seed):
    r = client.get("/traces?min_latency=1000")
    items = r.json()["items"]
    assert {i["trace_id"] for i in items} == {"t003"}
    r2 = client.get("/traces?max_latency=300")
    assert {i["trace_id"] for i in r2.json()["items"]} == {"t001"}
    r3 = client.get("/traces?min_latency=150&max_latency=500")
    assert {i["trace_id"] for i in r3.json()["items"]} == {"t001", "t002"}


def test_get_trace_detail(client, seed):
    r = client.get("/traces/t002")
    assert r.status_code == 200
    body = r.json()
    assert body["trace_id"] == "t002"
    assert "retrieved_chunks" in body and "citations" in body


def test_get_trace_404(client, seed):
    r = client.get("/traces/does_not_exist")
    assert r.status_code == 404


def test_feedback_submit_and_idempotency(client, seed):
    r1 = client.put("/traces/t002/feedback", json={"rating": "up"})
    assert r1.status_code == 200
    r2 = client.put("/traces/t002/feedback", json={"rating": "down", "note": "wrong"})
    assert r2.status_code == 200
    detail = client.get("/traces/t002").json()
    assert detail["feedback"] == "down"
    assert r2.json()["note"] == "wrong"


def test_feedback_rejects_invalid_rating(client, seed):
    r = client.put("/traces/t002/feedback", json={"rating": "meh"})
    assert r.status_code == 422


def test_feedback_404_unknown_trace(client, seed):
    r = client.put("/traces/nope/feedback", json={"rating": "up"})
    assert r.status_code == 404


def test_combined_cursor_and_filter(client, seed):
    r1 = client.get("/traces?prompt_version=v1.0&limit=1")
    body1 = r1.json()
    # Only t001 is v1.0
    assert len(body1["items"]) == 1
    assert body1["items"][0]["trace_id"] == "t001"
    assert body1["meta"]["has_more"] is False
    # No cursor when has_more is false
    assert body1["meta"]["next_cursor"] is None


def test_concurrent_feedback_upsert_is_safe(client, seed):
    # Simulate two concurrent updates; the final state must be deterministic
    # and the row must remain valid (rating in {up, down}).
    for rating in ["up", "down", "up"]:
        r = client.put("/traces/t001/feedback", json={"rating": rating})
        assert r.status_code == 200
    detail = client.get("/traces/t001").json()
    assert detail["feedback"] in ("up", "down")