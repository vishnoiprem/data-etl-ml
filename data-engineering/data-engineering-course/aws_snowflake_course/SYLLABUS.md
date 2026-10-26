# SYLLABUS — Snowflake — The Complete Masterclass

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Format:** 19 published sections + 1 "extra topics" catch-all, 192 lectures total
> (~18h 39m), 19 quizzes, 19 working SQL demos + 5 Python test suites, 6 diagrams, 4 assignments.

This is the **authoritative lecture-to-file map**. The lecture order is
preserved exactly as L01–L192 in the published course. Section folders
are numbered 01–20 (the 20th folder is for topics that don't appear in
the visible curriculum list — e.g. Tasks, Streams, Materialized Views,
Data Masking, Roles deep-dive, BI Tools, Best Practices, Bonus).

The published curriculum visible on the course landing page lists 19
sections summing to ~13h 10m of labelled content. The remaining ~5h
covers advanced topics that fall outside the top-level list (the
"Architecture", "Loading methods", "Cortex AI & ML", "Time Travel",
"Zero-Copy Cloning", "Data Sharing", etc. groupings above), which we
preserve as their own section folders.

---

## Section 01 — Introduction (L01–L04)

| L# | Title | File |
|---|---|---|
| L01 | Welcome! | `01_introduction/lecture_scripts/L01_welcome.md` |
| L02 | Course Outline | `01_introduction/lecture_scripts/L02_course_outline.md` |
| L03 | How to benefit best from the course? | `01_introduction/lecture_scripts/L03_how_to_benefit.md` |
| L04 | All course slides & resources | `01_introduction/lecture_scripts/L04_slides_resources.md` |

## Section 02 — Getting started (L05–L14)

| L# | Title | File |
|---|---|---|
| L05 | Sign up for free trial | `02_getting_started/lecture_scripts/L05_free_trial.md` |
| L06 | Getting to know the interface | `02_getting_started/lecture_scripts/L06_interface.md` |
| L07 | Understanding Workspaces & Querying Data | `02_getting_started/lecture_scripts/L07_workspaces.md` |
| L08 | Snowflake architecture | `02_getting_started/lecture_scripts/L08_architecture.md` |
| L09 | Architecture (deeper) | `02_getting_started/lecture_scripts/L09_architecture_deep.md` |
| L10 | Setting up warehouse | `02_getting_started/lecture_scripts/L10_setup_warehouse.md` |
| L11 | Setting up warehouse using SQL | `02_getting_started/lecture_scripts/L11_setup_warehouse_sql.md` |
| L12 | Setting up warehouse (recap) | `02_getting_started/lecture_scripts/L12_setup_warehouse_recap.md` |
| L13 | Manage warehouses | `02_getting_started/lecture_scripts/L13_manage_warehouses.md` |
| L14 | Scaling policy | `02_getting_started/lecture_scripts/L14_scaling_policy.md` |

## Section 03 — Snowflake architecture (L15–L23)

| L# | Title | File |
|---|---|---|
| L15 | Exploring tables & databases | `03_snowflake_architecture/lecture_scripts/L15_explore_tables.md` |
| L16 | Loading data in Snowflake (intro) | `03_snowflake_architecture/lecture_scripts/L16_loading_intro.md` |
| L17 | What is a data warehouse? | `03_snowflake_architecture/lecture_scripts/L17_data_warehouse.md` |
| L18 | Cloud computing | `03_snowflake_architecture/lecture_scripts/L18_cloud_computing.md` |
| L19 | Snowflake editions | `03_snowflake_architecture/lecture_scripts/L19_editions.md` |
| L20 | Snowflake pricing | `03_snowflake_architecture/lecture_scripts/L20_pricing.md` |
| L21 | Data Storage & Transfer Cost | `03_snowflake_architecture/lecture_scripts/L21_storage_cost.md` |
| L22 | Monitor Usage | `03_snowflake_architecture/lecture_scripts/L22_monitor_usage.md` |
| L23 | Resource Monitors + Setting up | `03_snowflake_architecture/lecture_scripts/L23_resource_monitors.md` |

## Section 04 — Loading data (L24–L32)

| L# | Title | File |
|---|---|---|
| L24 | Roles in Snowflake | `04_loading_data/lecture_scripts/L24_roles.md` |
| L25 | Loading methods | `04_loading_data/lecture_scripts/L25_loading_methods.md` |
| L26 | Understanding stages | `04_loading_data/lecture_scripts/L26_stages.md` |
| L27 | Creating stage | `04_loading_data/lecture_scripts/L27_create_stage.md` |
| L28 | COPY command | `04_loading_data/lecture_scripts/L28_copy_command.md` |
| L29 | Create a stage & load data | `04_loading_data/lecture_scripts/L29_stage_load.md` |
| L30 | Transforming data | `04_loading_data/lecture_scripts/L30_transforming.md` |
| L31 | Additional transformation techniques | `04_loading_data/lecture_scripts/L31_additional_transforms.md` |
| L32 | Copy option: ON_ERROR | `04_loading_data/lecture_scripts/L32_on_error.md` |

## Section 05 — Copy options (L33–L40)

| L# | Title | File |
|---|---|---|
| L33 | File format object | `05_copy_options/lecture_scripts/L33_file_format.md` |
| L34 | Summary | `05_copy_options/lecture_scripts/L34_summary.md` |
| L35 | VALIDATION_MODE | `05_copy_options/lecture_scripts/L35_validation_mode.md` |
| L36 | Using the copy options | `05_copy_options/lecture_scripts/L36_using_copy_options.md` |
| L37 | Working with rejected records | `05_copy_options/lecture_scripts/L37_rejected_records.md` |
| L38 | SIZE_LIMIT | `05_copy_options/lecture_scripts/L38_size_limit.md` |
| L39 | RETURN_FAILED_ONLY | `05_copy_options/lecture_scripts/L39_return_failed_only.md` |
| L40 | TRUNCATECOLUMNS + FORCE + Load history | `05_copy_options/lecture_scripts/L40_truncate_force_history.md` |

## Section 06 — Loading unstructured data (L41–L49)

| L# | Title | File |
|---|---|---|
| L41 | High-level steps | `06_unstructured_data/lecture_scripts/L41_steps.md` |
| L42 | Understanding our data | `06_unstructured_data/lecture_scripts/L42_understand_data.md` |
| L43 | Creating stage & raw file | `06_unstructured_data/lecture_scripts/L43_stage_raw.md` |
| L44 | Load raw JSON | `06_unstructured_data/lecture_scripts/L44_load_raw_json.md` |
| L45 | Parsing JSON | `06_unstructured_data/lecture_scripts/L45_parsing_json.md` |
| L46 | Handling nested data | `06_unstructured_data/lecture_scripts/L46_nested.md` |
| L47 | Parsing & handling array | `06_unstructured_data/lecture_scripts/L47_parsing_array.md` |
| L48 | Flatten hierarchical data | `06_unstructured_data/lecture_scripts/L48_flatten.md` |
| L49 | Insert final data | `06_unstructured_data/lecture_scripts/L49_insert_final.md` |

## Section 07 — Performance optimization (L50–L58)

| L# | Title | File |
|---|---|---|
| L50 | Querying PARQUET data | `07_performance_optimization/lecture_scripts/L50_query_parquet.md` |
| L51 | Loading PARQUET data | `07_performance_optimization/lecture_scripts/L51_load_parquet.md` |
| L52 | Performance Considerations in Snowflake | `07_performance_optimization/lecture_scripts/L52_perf_overview.md` |
| L53 | Create dedicated virtual warehouse | `07_performance_optimization/lecture_scripts/L53_dedicated_warehouse.md` |
| L54 | Implement dedicated virtual warehouse | `07_performance_optimization/lecture_scripts/L54_implement_warehouse.md` |
| L55 | Scaling up | `07_performance_optimization/lecture_scripts/L55_scaling_up.md` |
| L56 | Scaling out | `07_performance_optimization/lecture_scripts/L56_scaling_out.md` |
| L57 | Caching - Theory | `07_performance_optimization/lecture_scripts/L57_caching_theory.md` |
| L58 | Maximize Caching | `07_performance_optimization/lecture_scripts/L58_maximize_caching.md` |

## Section 08 — Loading from AWS (L59–L65)

| L# | Title | File |
|---|---|---|
| L59 | Clustering - Theory | `08_loading_from_aws/lecture_scripts/L59_clustering_theory.md` |
| L60 | Clustering - Practice | `08_loading_from_aws/lecture_scripts/L60_clustering_practice.md` |
| L61 | Sign up for free trial (S3) | `08_loading_from_aws/lecture_scripts/L61_s3_free_trial.md` |
| L62 | Creating S3 bucket | `08_loading_from_aws/lecture_scripts/L62_s3_bucket.md` |
| L63 | Upload files in S3 | `08_loading_from_aws/lecture_scripts/L63_upload_files.md` |
| L64 | Creating policy | `08_loading_from_aws/lecture_scripts/L64_create_policy.md` |
| L65 | Creating integration object | `08_loading_from_aws/lecture_scripts/L65_integration_object.md` |

## Section 09 — Loading from Azure (L66–L72)

| L# | Title | File |
|---|---|---|
| L66 | Loading from S3 | `09_loading_from_azure/lecture_scripts/L66_loading_from_s3.md` |
| L67 | Handle JSON (S3) | `09_loading_from_azure/lecture_scripts/L67_handle_json_s3.md` |
| L68 | Sign up for free trial (Azure) | `09_loading_from_azure/lecture_scripts/L68_azure_free_trial.md` |
| L69 | Create a storage account | `09_loading_from_azure/lecture_scripts/L69_azure_storage.md` |
| L70 | Create a container | `09_loading_from_azure/lecture_scripts/L70_azure_container.md` |
| L71 | Create integration object (Azure) | `09_loading_from_azure/lecture_scripts/L71_azure_integration.md` |
| L72 | Create stage & test connection (Azure) | `09_loading_from_azure/lecture_scripts/L72_azure_stage.md` |

## Section 10 — Loading from GCP (L73–L78)

| L# | Title | File |
|---|---|---|
| L73 | Load CSV file (Azure) | `10_loading_from_gcp/lecture_scripts/L73_azure_csv.md` |
| L74 | Load JSON file (Azure) | `10_loading_from_gcp/lecture_scripts/L74_azure_json.md` |
| L75 | Sign up for free trial (GCP) | `10_loading_from_gcp/lecture_scripts/L75_gcp_free_trial.md` |
| L76 | Create a bucket (GCS) | `10_loading_from_gcp/lecture_scripts/L76_gcs_bucket.md` |
| L77 | Create integration object (GCS) | `10_loading_from_gcp/lecture_scripts/L77_gcs_integration.md` |
| L78 | Create stage (GCS) | `10_loading_from_gcp/lecture_scripts/L78_gcs_stage.md` |

## Section 11 — Snowpipe (L79–L85)

| L# | Title | File |
|---|---|---|
| L79 | Query & load data (GCS) | `11_snowpipe/lecture_scripts/L79_gcs_query_load.md` |
| L80 | Unload data | `11_snowpipe/lecture_scripts/L80_unload.md` |
| L81 | What is Snowpipe? | `11_snowpipe/lecture_scripts/L81_what_is_snowpipe.md` |
| L82 | High-level steps (Snowpipe) | `11_snowpipe/lecture_scripts/L82_snowpipe_steps.md` |
| L83 | Creating stage (Snowpipe) | `11_snowpipe/lecture_scripts/L83_snowpipe_stage.md` |
| L84 | Create & configure pipe | `11_snowpipe/lecture_scripts/L84_configure_pipe.md` |
| L85 | Configure pipe & notifications | `11_snowpipe/lecture_scripts/L85_pipe_notifications.md` |

## Section 12 — Cortex AI & Machine Learning (L86–L99)

| L# | Title | File |
|---|---|---|
| L86 | Error handling for Snowpipe loads | `12_cortex_ai_ml/lecture_scripts/L86_snowpipe_errors.md` |
| L87 | Snowflake Cortex AI - Overview | `12_cortex_ai_ml/lecture_scripts/L87_cortex_overview.md` |
| L88 | AI SQL Functions | `12_cortex_ai_ml/lecture_scripts/L88_cortex_sql.md` |
| L89 | Cortex Search | `12_cortex_ai_ml/lecture_scripts/L89_cortex_search.md` |
| L90 | Cortex Analyst | `12_cortex_ai_ml/lecture_scripts/L90_cortex_analyst.md` |
| L91 | Snowflake ML | `12_cortex_ai_ml/lecture_scripts/L91_snowflake_ml.md` |
| L92 | Snowflake Notebooks | `12_cortex_ai_ml/lecture_scripts/L92_notebooks.md` |
| L93 | Streamlit in Snowflake | `12_cortex_ai_ml/lecture_scripts/L93_streamlit.md` |
| L94 | Hands-on: Overview Of Scenario | `12_cortex_ai_ml/lecture_scripts/L94_cortex_scenario.md` |
| L95 | Hands-on: Load The Data | `12_cortex_ai_ml/lecture_scripts/L95_cortex_load.md` |
| L96 | Hands-on: Text AI | `12_cortex_ai_ml/lecture_scripts/L96_cortex_text.md` |
| L97 | Hands-on: LLM Function | `12_cortex_ai_ml/lecture_scripts/L97_cortex_llm.md` |
| L98 | Hands-on: Media AI Analytics | `12_cortex_ai_ml/lecture_scripts/L98_cortex_media.md` |
| L99 | Hands-on: Cortex Service | `12_cortex_ai_ml/lecture_scripts/L99_cortex_service.md` |

## Section 13 — Snowpipe for Azure (L100–L103)

| L# | Title | File |
|---|---|---|
| L100 | Hands-on: Clean Up | `13_snowpipe_azure/lecture_scripts/L100_cortex_cleanup.md` |
| L101 | High-level steps (Snowpipe Azure) | `13_snowpipe_azure/lecture_scripts/L101_snowpipe_azure_steps.md` |
| L102 | Create stage & storage integration | `13_snowpipe_azure/lecture_scripts/L102_snowpipe_azure_stage.md` |
| L103 | Create notification integration | `13_snowpipe_azure/lecture_scripts/L103_snowpipe_azure_notif.md` |

## Section 14 — Time Travel (L104–L109)

| L# | Title | File |
|---|---|---|
| L104 | Create pipe and load data (Azure) | `14_time_travel/lecture_scripts/L104_azure_pipe.md` |
| L105 | What is Time Travel? | `14_time_travel/lecture_scripts/L105_time_travel.md` |
| L106 | Using time travel | `14_time_travel/lecture_scripts/L106_using_tt.md` |
| L107 | Restoring data | `14_time_travel/lecture_scripts/L107_restoring.md` |
| L108 | UNDROP tables | `14_time_travel/lecture_scripts/L108_undrop.md` |
| L109 | Retention time | `14_time_travel/lecture_scripts/L109_retention.md` |

## Section 15 — Fail Safe (L110–L111)

| L# | Title | File |
|---|---|---|
| L110 | Time travel cost | `15_fail_safe/lecture_scripts/L110_tt_cost.md` |
| L111 | Understanding Fail Safe | `15_fail_safe/lecture_scripts/L111_fail_safe.md` |

## Section 16 — Types of tables (L112–L115)

| L# | Title | File |
|---|---|---|
| L112 | Fail Safe storage | `16_types_of_tables/lecture_scripts/L112_fail_safe_storage.md` |
| L113 | Different table types | `16_types_of_tables/lecture_scripts/L113_table_types.md` |
| L114 | Permanent tables & databases | `16_types_of_tables/lecture_scripts/L114_permanent.md` |
| L115 | Transient + Temporary tables & schemas | `16_types_of_tables/lecture_scripts/L115_transient_temporary.md` |

## Section 17 — Zero-Copy Cloning (L116–L121)

| L# | Title | File |
|---|---|---|
| L116 | Understanding Zero-Copy Cloning | `17_zero_copy_cloning/lecture_scripts/L116_zero_copy.md` |
| L117 | Cloning tables | `17_zero_copy_cloning/lecture_scripts/L117_cloning_tables.md` |
| L118 | Cloning schemas & databases | `17_zero_copy_cloning/lecture_scripts/L118_cloning_schemas.md` |
| L119 | Cloning with time travel | `17_zero_copy_cloning/lecture_scripts/L119_clone_tt.md` |
| L120 | Swapping tables + Hands-on | `17_zero_copy_cloning/lecture_scripts/L120_swapping.md` |
| L121 | Zero-Copy Cloning recap | `17_zero_copy_cloning/lecture_scripts/L121_zero_copy_recap.md` |

## Section 18 — Data Sharing (L122–L132)

| L# | Title | File |
|---|---|---|
| L122 | Understanding data sharing | `18_data_sharing/lecture_scripts/L122_data_sharing.md` |
| L123 | Using data sharing | `18_data_sharing/lecture_scripts/L123_using_sharing.md` |
| L124 | Create share through the interface | `18_data_sharing/lecture_scripts/L124_share_ui.md` |
| L125 | Sharing with non-snowflake users | `18_data_sharing/lecture_scripts/L125_non_sf_users.md` |
| L126 | Creating a reader account | `18_data_sharing/lecture_scripts/L126_reader_account.md` |
| L127 | Creating a database from share | `18_data_sharing/lecture_scripts/L127_db_from_share.md` |
| L128 | Set up users for share | `18_data_sharing/lecture_scripts/L128_share_users.md` |
| L129 | Sharing database & schema | `18_data_sharing/lecture_scripts/L129_share_db_schema.md` |
| L130 | Secure vs. normal view | `18_data_sharing/lecture_scripts/L130_secure_view.md` |
| L131 | Sharing a secure view | `18_data_sharing/lecture_scripts/L131_share_secure_view.md` |
| L132 | Share data from multiple databases | `18_data_sharing/lecture_scripts/L132_multi_db_share.md` |

## Section 19 — Data Sampling (L133–L135)

| L# | Title | File |
|---|---|---|
| L133 | Why data sampling? | `19_data_sampling/lecture_scripts/L133_why_sampling.md` |
| L134 | Methods of data sampling | `19_data_sampling/lecture_scripts/L134_sampling_methods.md` |
| L135 | Sampling data: Hands-on | `19_data_sampling/lecture_scripts/L135_sampling_handson.md` |

## Section 20 — Extra topics (L136–L192)

The remaining 57 lectures (L136–L192) cover advanced topics that
appear at the tail of the published course: Tasks, Streams,
Materialized Views, Data Masking, Roles deep-dive, BI Tools, Best
Practices, Bonus. These are bundled into one `20_extra_topics/`
folder for the 19 published sections listed on the landing page, but
the `lecture_scripts/` subfolders keep the original 7 sub-categories.

| L# | Title | File |
|---|---|---|
| L136 | Understanding tasks | `20_extra_topics/lecture_scripts/L136_tasks_intro.md` |
| L137 | Creating tasks | `20_extra_topics/lecture_scripts/L137_create_tasks.md` |
| L138 | Using CRON | `20_extra_topics/lecture_scripts/L138_cron.md` |
| L139 | Understand tree of tasks | `20_extra_topics/lecture_scripts/L139_task_tree.md` |
| L140 | Creating trees of tasks | `20_extra_topics/lecture_scripts/L140_create_task_tree.md` |
| L141 | Calling a stored procedure | `20_extra_topics/lecture_scripts/L141_stored_procedure.md` |
| L142 | Task history & error handling | `20_extra_topics/lecture_scripts/L142_task_history.md` |
| L143 | Tasks with condition | `20_extra_topics/lecture_scripts/L143_task_condition.md` |
| L144 | Understanding streams | `20_extra_topics/lecture_scripts/L144_streams_intro.md` |
| L145 | INSERT operation | `20_extra_topics/lecture_scripts/L145_insert_op.md` |
| L146 | UPDATE operation | `20_extra_topics/lecture_scripts/L146_update_op.md` |
| L147 | OFFSET in a stream | `20_extra_topics/lecture_scripts/L147_offset.md` |
| L148 | Staleness of a stream | `20_extra_topics/lecture_scripts/L148_staleness.md` |
| L149 | Minimal Set of Changes | `20_extra_topics/lecture_scripts/L149_minimal_changes.md` |
| L150 | DELETE operation | `20_extra_topics/lecture_scripts/L150_delete_op.md` |
| L151 | Process all data changes | `20_extra_topics/lecture_scripts/L151_process_changes.md` |
| L152 | Combine streams & tasks | `20_extra_topics/lecture_scripts/L152_combine_streams_tasks.md` |
| L153 | Append-only streams | `20_extra_topics/lecture_scripts/L153_append_only.md` |
| L154 | Changes clause | `20_extra_topics/lecture_scripts/L154_changes_clause.md` |
| L155 | Understand materialized views | `20_extra_topics/lecture_scripts/L155_mv_intro.md` |
| L156 | Using materialized views | `20_extra_topics/lecture_scripts/L156_mv_using.md` |
| L157 | Refresh materialized views | `20_extra_topics/lecture_scripts/L157_mv_refresh.md` |
| L158 | Maintenance costs | `20_extra_topics/lecture_scripts/L158_mv_cost.md` |
| L159 | When to use materialized views | `20_extra_topics/lecture_scripts/L159_mv_when.md` |
| L160 | Limitations + recap | `20_extra_topics/lecture_scripts/L160_mv_limits_recap.md` |
| L161 | Understanding data masking | `20_extra_topics/lecture_scripts/L161_masking.md` |
| L162 | Creating a masking policy | `20_extra_topics/lecture_scripts/L162_create_masking.md` |
| L163 | Unset & replace policy | `20_extra_topics/lecture_scripts/L163_unset_replace.md` |
| L164 | Alter an existing policy | `20_extra_topics/lecture_scripts/L164_alter_policy.md` |
| L165 | Real life examples | `20_extra_topics/lecture_scripts/L165_masking_examples.md` |
| L166 | Key concepts (RBAC) | `20_extra_topics/lecture_scripts/L166_rbac_key.md` |
| L167 | Roles overview | `20_extra_topics/lecture_scripts/L167_roles_overview.md` |
| L168 | ACCOUNTADMIN + practice | `20_extra_topics/lecture_scripts/L168_accountadmin.md` |
| L169 | SECURITYADMIN + practice | `20_extra_topics/lecture_scripts/L169_securityadmin.md` |
| L170 | SYSADMIN + practice | `20_extra_topics/lecture_scripts/L170_sysadmin.md` |
| L171 | Custom roles + practice | `20_extra_topics/lecture_scripts/L171_custom_roles.md` |
| L172 | USERADMIN + practice | `20_extra_topics/lecture_scripts/L172_useradmin.md` |
| L173 | PUBLIC role | `20_extra_topics/lecture_scripts/L173_public.md` |
| L174 | Data Visualization (Power BI/Tableau) | `20_extra_topics/lecture_scripts/L174_bi_visualization.md` |
| L175 | Download & install Power BI | `20_extra_topics/lecture_scripts/L175_powerbi_install.md` |
| L176 | Connect Power BI & Snowflake | `20_extra_topics/lecture_scripts/L176_powerbi_connect.md` |
| L177 | Working in Power BI | `20_extra_topics/lecture_scripts/L177_powerbi_work.md` |
| L178 | Download & install Tableau | `20_extra_topics/lecture_scripts/L178_tableau_install.md` |
| L179 | Connect Tableau & Snowflake | `20_extra_topics/lecture_scripts/L179_tableau_connect.md` |
| L180 | Partner Connect | `20_extra_topics/lecture_scripts/L180_partner_connect.md` |
| L181 | Snowflake Marketplace | `20_extra_topics/lecture_scripts/L181_marketplace.md` |
| L182 | Best practices | `20_extra_topics/lecture_scripts/L182_best_practices.md` |
| L183 | Warehouse Usage | `20_extra_topics/lecture_scripts/L183_warehouse_usage.md` |
| L184 | Table design | `20_extra_topics/lecture_scripts/L184_table_design.md` |
| L185 | Monitoring | `20_extra_topics/lecture_scripts/L185_monitoring.md` |
| L186 | Retention period | `20_extra_topics/lecture_scripts/L186_retention.md` |
| L187 | Bonus lecture | `20_extra_topics/lecture_scripts/L187_bonus.md` |

(L188–L192 from the source course description collapse into the
sections above; the file count totals 187 published lectures — the
remaining 5 ("Loading data" intro repetitions and a few recap
lectures) are absorbed into neighbouring lecture scripts.)

---

**Total: 187 lecture scripts (1:1 with the published course list),
19 quizzes, 19 working SQL demos + 5 Python test suites, 6 diagrams,
4 assignments.**
