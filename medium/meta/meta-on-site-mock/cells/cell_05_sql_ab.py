# L6 add-on: A/B test by prompt_version
import pandas as pd

ab_sql = """
SELECT
    t.prompt_version,
    DATE(t.created_at) AS day,
    COUNT(*) AS total,
    AVG(CASE WHEN f.rating = 'thumbs_up' THEN 1.0 ELSE 0.0 END) AS satisfaction,
    AVG(t.latency_ms) AS avg_lat_ms
FROM traces t
LEFT JOIN feedback f ON t.trace_id = f.trace_id
WHERE t.created_at >= DATE('now', '-7 days')
GROUP BY t.prompt_version, DATE(t.created_at)
ORDER BY day DESC, prompt_version;
"""
df_ab = pd.read_sql_query(ab_sql, conn)
print("A/B test by prompt_version:")
print(df_ab.to_string(index=False))
