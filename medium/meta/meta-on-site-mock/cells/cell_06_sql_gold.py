# L6 add-on: build the gold eval set from corrected_answer
gold_sql = """
SELECT
    t.query,
    t.response AS model_answer,
    f.corrected_answer AS human_answer,
    t.prompt_version
FROM traces t
JOIN feedback f ON t.trace_id = f.trace_id
WHERE f.corrected_answer IS NOT NULL
ORDER BY t.created_at DESC
LIMIT 5;
"""
df_gold = pd.read_sql_query(gold_sql, conn)
print("Gold eval set sample (rows where humans corrected the model):")
print(df_gold.to_string(index=False))
print()
print("-> This is your labeled data for offline eval. Replay new prompts against")
print("  this set BEFORE shipping. If satisfaction drops, do not ship.")
