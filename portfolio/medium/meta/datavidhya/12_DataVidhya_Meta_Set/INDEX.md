# Meta-tagged DataVidhya problems — file index

Every one of the **76** problems behind the site's Meta company filter
(all 4 pages), plus 5 data-modeling questions with no site equivalent.
81 files total.

Coverage: 10 Easy, 47 Medium, 19 Hard — matching the site's own difficulty split.

Files `26`-`81` were built against the site's published schema, sample rows
and expected output (via `datavidhya.com/api/v1/questions/<slug>/`), so a
green run means the answer matches the grader's.

Run any file directly — each is self-contained and self-asserting:

```bash
../../../../.env/bin/python 37_window_multiple_rankings.py
```

| # | Problem | Difficulty | Topics | Slug | File |
|---|---|---|---|---|---|
| 01 | Facebook Power Users (High Engagement) | Hard | Aggregate Functions | `aggregation-facebook-power-users` | `01_power_users.py` |
| 02 | 7-Day Retention Cohort Analysis | Hard | CTEs, Date Functions | `ctes-7day-retention-cohort-analysis` | `02_weekly_retention_cohort.py` |
| 03 | Event Funnel Drop-Off Analysis | Hard | Joins, CTEs | `funnel-event-dropoff-analysis` | `03_funnel_dropoff.py` |
| 04 | Monthly Active User Retention | Medium | Joins, Date Functions | `joins-monthly-active-user-retention` | `04_monthly_active_retention.py` |
| 05 | Pages With No Likes | Easy | Left Join, NULL Handling | `joins-pages-with-no-likes` | `05_pages_with_no_likes.py` |
| 06 | Monthly Active, Churned, and Resurrected Users | Medium | Windows, CTEs | `monthly-active-churned-resurrected` | `06_mau_churn_resurrect.py` |
| 07 | Highest Energy Consumption Year | Medium | UNION ALL, Aggregation | `aggregation-highest-energy-consumption-year` | `07_highest_energy_year.py` |
| 08 | Customer Revenue in March | Medium | Date Functions, Aggregation | `aggregation-customer-revenue-march` | `08_march_revenue_per_customer.py` |
| 09 | Top 5th Percentile Fraud Score Per State | Hard | Window Functions | `window-functions-top-percentile-fraud-score` | `09_top_percentile_fraud.py` |
| 10 | Friend Request Acceptance Rate | Medium | Aggregation | `aggregation-friend-request-acceptance-rate` | `10_friend_request_acceptance.py` |
| 11 | Campaign Success Rate by Language | Medium | Aggregation | `aggregation-campaign-success-by-language` | `11_campaign_success_by_language.py` |
| 12 | Monthly Revenue Percentage Change | Medium | Windows, Date Functions | `window-functions-monthly-revenue-pct-change` | `12_mom_revenue_change.py` |
| 13 | Popularity Percentage by Domain | Hard | Aggregation + Window | `aggregation-popularity-pct-by-domain` | `13_popularity_by_domain.py` |
| 14 | Days Between First and Last Post | Medium | Date Functions, Aggregation | `aggregation-days-between-first-last-post` | `14_days_first_last_post.py` |
| 15 | Running Distinct Count of Users | Hard | CTEs | `running-distinct-count` | `15_running_distinct_users.py` |
| 16 | Spam Post Percentage by Day | Medium | Joins, String Manipulation | `aggregation-spam-post-percentage-by-day` | `16_spam_post_percentage.py` |
| 17 | Advertiser Payment Status Classification | Hard | Joins, CASE WHEN | `case-when-advertiser-payment-status` | `17_advertiser_payment_status.py` |
| 18 | Average Friend Requests Sent Per Week | Medium | Date Functions, Aggregation | `aggregation-avg-friend-requests-per-week` | `18_avg_requests_per_week.py` |
| 19 | User with Most Friends (Bidirectional) | Medium | Aggregation, Union | `aggregation-user-most-friends-bidirectional` | `19_most_friends_bidirectional.py` |
| 20 | Conversion Rate from View to Lead by Location | Medium | Joins, Aggregation | `aggregation-conversion-rate-view-to-lead` | `20_view_to_lead_conversion.py` |
| 21 | Notification System | Medium | Data Model — OLTP relational | *modeling — no site equivalent* | `21_model_notification_system.py` |
| 22 | Social Media Platform | Medium | Data Model — OLTP relational | *modeling — no site equivalent* | `22_model_social_media_platform.py` |
| 23 | Product Funnel & Conversion Analytics | Medium | Dim Model — star schema | *modeling — no site equivalent* | `23_model_product_funnel_star.py` |
| 24 | Ad Platform Click & Impression Analytics | Medium | Dim Model — star schema | *modeling — no site equivalent* | `24_model_ad_platform_star.py` |
| 25 | Notification Delivery Analytics | Medium | Dim Model — star schema | *modeling — no site equivalent* | `25_model_notification_delivery_analytics.py` |
| 26 | Create Features from Text | Hard | String Manipulation, Feature Engineering | `text-features` | `26_text_features.py` |
| 27 | Cumulative Rank with Reset (Session Running Total) | Hard | Window Functions, Session Analysis | `session-running-total` | `27_session_running_total.py` |
| 28 | Handle Data Skew in Joins | Hard | Inner Joins, Data Skew, Optimization, Partitioning | `handle-data-skew-joins` | `28_data_skew_joins.py` |
| 29 | Index Strategy for Performance | Hard | Aggregate Functions, Index Strategy, Performance Tuning | `index-strategy-performance` | `29_index_strategy.py` |
| 30 | Nth Highest Salary | Hard | Window Functions, Subqueries | `nth-highest-salary` | `30_nth_highest_salary.py` |
| 31 | Popularity Percentage | Hard | Subqueries, Aggregate Functions | `popularity-percentage` | `31_popularity_percentage.py` |
| 32 | Recursive CTE for Hierarchical Data | Hard | Common Table Expressions | `recursive-cte-hierarchical-data` | `32_recursive_cte_hierarchy.py` |
| 33 | Rolling 7-Day Active User Count | Hard | Date/Time Functions, Analytics | `rolling-7day-active-users` | `33_rolling_7day_active_users.py` |
| 34 | Sentiment Analysis on Text | Hard | CASE WHEN, String Manipulation, Aggregate Functions | `sentiment-analysis-text` | `34_sentiment_analysis_text.py` |
| 35 | Top 5 Products with Promotion Analysis | Hard | Inner Joins, CASE WHEN, Aggregate Functions | `aggregation-top5-products-promo-analysis` | `35_top5_products_promo.py` |
| 36 | User Popularity Score | Hard | Common Table Expressions, Aggregate Functions | `user-popularity-score` | `36_user_popularity_score.py` |
| 37 | Window Function Optimization | Hard | Window Functions | `window-function-multiple-rankings` | `37_window_multiple_rankings.py` |
| 38 | 3 Most Recent Posts Per User | Medium | Window Functions | `ranking-3-most-recent-posts-per-user` | `38_three_recent_posts_per_user.py` |
| 39 | Acceptance Rate By Date | Medium | Inner Joins, CTEs, Date/Time Functions | `friend-request-acceptance-rate` | `39_acceptance_rate_by_date.py` |
| 40 | Active Users Retention | Medium | Date/Time Functions, Aggregate Functions | `active-users-retention` | `40_active_users_retention.py` |
| 41 | App Click-Through Rate (CTR) | Medium | CASE WHEN, Aggregate Functions | `aggregation-app-click-through-rate` | `41_app_click_through_rate.py` |
| 42 | Approximate Quantiles and Percentiles | Medium | Mathematical Functions, Aggregate Functions | `approximate-quantiles-percentiles` | `42_quantiles_percentiles.py` |
| 43 | Avg Salary by Dept vs Company | Medium | Window Functions | `window-functions-dept-avg-vs-company-avg` | `43_dept_avg_vs_company_avg.py` |
| 44 | Chat Messages Schema Analysis | Medium | Aggregate Functions | `chat-messages-schema-analysis` | `44_chat_messages_schema_analysis.py` |
| 45 | Comments Histogram by Users | Medium | Subqueries, Aggregate Functions | `comments-histogram-by-users` | `45_comments_histogram.py` |
| 46 | Consecutive Numbers | Medium | Window Functions, Gap And Island | `consecutive-numbers` | `46_consecutive_numbers.py` |
| 47 | Consistent Monthly Shoppers | Medium | Aggregate Functions | `consistent-monthly-shoppers` | `47_consistent_monthly_shoppers.py` |
| 48 | Coverage Analysis: Data Quality Check | Medium | Inner Joins, Aggregate Functions, Data Quality | `coverage-analysis-data-quality` | `48_coverage_data_quality.py` |
| 49 | Deduplication Across Multiple Columns | Medium | Window Functions, Deduplication | `deduplication-multi-column` | `49_deduplication_multi_column.py` |
| 50 | Find Mutual Friends Between Two Users | Medium | Self Joins | `mutual-friends` | `50_mutual_friends.py` |
| 51 | Find all posts which were reacted to with a heart | Medium | Inner Joins, Aggregate Functions | `find-all-posts-which-were-reacted-to-with-a-heart` | `51_posts_reacted_with_heart.py` |
| 52 | Friday Likes from Friends Only | Medium | Inner Joins, Date/Time Functions | `joins-friday-likes-from-friends` | `52_friday_likes_from_friends.py` |
| 53 | Get Top N Records per Group | Medium | Window Functions, Aggregate Functions | `top-n-records-per-group` | `53_top_n_per_group.py` |
| 54 | Identify and Handle Outliers | Medium | Mathematical Functions | `identify-outliers` | `54_identify_outliers.py` |
| 55 | Marketing Campaign Effectiveness | Medium | Inner Joins, Aggregate Functions | `marketing-campaign` | `55_marketing_campaign.py` |
| 56 | Max Salary from Each Department | Medium | Inner Joins, Aggregate Functions | `max-salary-per-dept` | `56_max_salary_per_dept.py` |
| 57 | Merge Multiple DataFrames | Medium | Inner Joins, Aggregate Functions, Merges | `merge-multiple-dataframes` | `57_merge_multiple_dataframes.py` |
| 58 | Monthly Active Users (MAU) with Trend | Medium | Window Functions, Aggregate Functions | `monthly-active-users-mau-trend` | `58_mau_trend.py` |
| 59 | Most Active Users On Messenger | Medium | Window Functions, Aggregate Functions | `most-active-users-on-messenger` | `59_most_active_messenger_users.py` |
| 60 | Most Recent Record per Group | Medium | Window Functions, Deduplication | `most-recent-address` | `60_most_recent_address.py` |
| 61 | Pandas Apply with Lambda Functions | Medium | Date/Time, Pandas, Apply, Lambda | `pandas-apply-lambda` | `61_pandas_apply_lambda.py` |
| 62 | Peak Energy Usage Period | Medium | Aggregate Functions, Union | `peak-energy-usage-period` | `62_peak_energy_usage.py` |
| 63 | Rank and Dense Rank by Group | Medium | Window Functions, Partitioning | `rank-dense-rank` | `63_rank_dense_rank.py` |
| 64 | Returning User Detection | Medium | Self Joins, Mathematical Functions | `returning-user-detection` | `64_returning_user_detection.py` |
| 65 | Rolling Window Calculations | Medium | Window Functions, Time Series Analysis | `rolling-window` | `65_rolling_window.py` |
| 66 | Sampling and Stratified Selection | Medium | Window Functions, Sampling | `stratified-sampling` | `66_stratified_sampling.py` |
| 67 | Statistical Calculations per Group | Medium | Mathematical Functions, Aggregate Functions | `statistical-calculations` | `67_statistical_calculations.py` |
| 68 | String Parsing and JSON-like Extraction | Medium | ETL, String Manipulation, Regex | `string-parsing-json` | `68_string_parsing_json.py` |
| 69 | Unique Logins by User on facebook.com | Medium | Date/Time Functions | `unique-logins-facebook` | `69_unique_logins_facebook.py` |
| 70 | User Retention | Medium | Date/Time Functions, Aggregate Functions | `user-retention` | `70_user_retention_span.py` |
| 71 | User Signup Activation Rate | Medium | Casting, Inner Joins, Aggregate Functions | `user-signup-activation-rate` | `71_signup_activation_rate.py` |
| 72 | Users by Average Session Time | Medium | Date/Time Functions, Aggregate Functions | `aggregation-users-avg-session-time` | `72_avg_session_time.py` |
| 73 | Customer Download Trend Analysis | Easy | Aggregate Functions | `customer-download-trend-analysis` | `73_customer_download_trend.py` |
| 74 | Duplicate Job Listings | Easy | Aggregate Functions, Deduplication | `duplicate-job-listings` | `74_duplicate_job_listings.py` |
| 75 | Email Validation Filter | Easy | Regular Expression | `email-validation-filter` | `75_email_validation_filter.py` |
| 76 | Japanese City Population Sum | Easy | Aggregate Functions | `japanese-city-population-sum` | `76_japanese_city_population.py` |
| 77 | Low-Fat Recyclable Products | Easy | Filter | `filtering-low-fat-recyclable-products` | `77_low_fat_recyclable.py` |
| 78 | Social Media PII Extraction | Easy | String Manipulation | `social-media-pii-extraction` | `78_social_media_pii_extraction.py` |
| 79 | Social Media Text Correction | Easy | Regular Expression | `social-media-text-correction` | `79_social_media_text_correction.py` |
| 80 | Third Highest Product Price | Easy | Window Functions, Dense_rank, Pandas | `third-highest-product-price` | `80_third_highest_product_price.py` |
| 81 | Unique User Activity Count | Easy | Left Outer Joins | `unique-user-activity-count` | `81_unique_user_activity_count.py` |
