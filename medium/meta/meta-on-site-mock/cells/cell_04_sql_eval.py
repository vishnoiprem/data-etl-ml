# Q4 SQL answer: measure RAG quality from traces + feedback
eval_sql = """
SELECT
    DATE(t.created_at) AS day,
    COUNT(*) AS total_traces,
    AVG(CASE WHEN f.rating = 'thumbs_up' THEN 1.0 ELSE 0.0 END) AS satisfaction,
    AVG(t.latency_ms) AS avg_latency_ms,
    SUM(t.cost_tokens) AS total_cost_tokens
FROM traces t
LEFT JOIN feedback f ON t.trace_id = f.trace_id
WHERE t.created_at >= DATE('now', '-7 days')
GROUP BY DATE(t.created_at)
ORDER BY day DESC;
"""
df = pd.read_sql_query(eval_sql, conn)
print(df.to_string(index=False))
