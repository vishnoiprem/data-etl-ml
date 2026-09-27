-- =====================================================================
-- Reviewer Queue Assignment — workload-balanced, skill-matched
-- =====================================================================

-- 1) Pick next reviewer for a given class + priority
WITH eligible_reviewers AS (
    SELECT r.reviewer_id,
           r.skills,
           r.timezone,
           r.max_concurrent,
           COALESCE(w.active_count, 0) AS active_count,
           r.max_concurrent - COALESCE(w.active_count, 0) AS capacity_left
    FROM reviewers r
    LEFT JOIN (
        SELECT assigned_to, COUNT(*) AS active_count
        FROM review_queue
        WHERE status IN ('PENDING', 'ASSIGNED')
        GROUP BY assigned_to
    ) w ON r.reviewer_id = w.assigned_to
    WHERE r.is_active = TRUE
      AND r.skills CONTAINS :required_skill      -- e.g. 'csam', 'hate_speech'
      AND COALESCE(w.active_count, 0) < r.max_concurrent
      -- timezone window: reviewer is 'awake'
      AND HOUR(NOW() AT TIME ZONE r.timezone) BETWEEN 8 AND 22
),
scored AS (
    SELECT
        reviewer_id,
        capacity_left,
        -- Prefer reviewers with more capacity
        capacity_left * 10
        -- Prefer reviewers in same timezone as content (faster review)
        - ABS(EXTRACT(HOUR FROM (NOW() AT TIME ZONE timezone)) -
              EXTRACT(HOUR FROM (NOW() AT TIME ZONE :content_tz))) * 0.1
        AS score
    FROM eligible_reviewers
)
SELECT reviewer_id
FROM scored
ORDER BY score DESC, capacity_left DESC
LIMIT 1;
