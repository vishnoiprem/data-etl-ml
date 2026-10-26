# SYLLABUS — dbt + Snowflake Analytics Engineering Cert Prep

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Format:** 19 sections, 131 lectures, ~11h 57m of content.
> 19 quizzes, 6 mermaid diagrams, 4 assignments, ~30 dbt project files + 15 pytest test files.

This is the **authoritative lecture-to-file map**. Section folders
are numbered `01_section/` … `19_section/`. Each section holds
its `README.md`, `lecture_scripts/`, and (where applicable) `code/`.

The **shared dbt project** lives in `dbt_project/` and grows
lecture by lecture — every section that introduces a new model,
macro, test, snapshot, or selector adds the file there.

---

## Section 01 — Welcome, Setup, dbt init (L01–L16)

| L# | Title | Min | File |
|---|---|---|---|
| L01 | Welcome & Course Philosophy | 2:47 | `01_section/lecture_scripts/L01_welcome_course_philosophy.md` |
| L02 | Course Roadmap - How to Navigate | 1:01 | `01_section/lecture_scripts/L02_course_roadmap_how_to_navigate.md` |
| L03 | Important Certification Exam Update (June 2026) | 0:40 | `01_section/lecture_scripts/L03_important_certification_exam_update_june_2026.md` |
| L04 | Course Setup: Discord Community | 0:49 | `01_section/lecture_scripts/L04_course_setup_discord_community.md` |
| L05 | Discord Community Invite | 0:20 | `01_section/lecture_scripts/L05_discord_community_invite.md` |
| L06 | Snowflake Setup | 5:24 | `01_section/lecture_scripts/L06_snowflake_setup.md` |
| L07 | Stage Creation | 3:26 | `01_section/lecture_scripts/L07_stage_creation.md` |
| L08 | Raw Tables Setup & Data Loading (COPY INTO) | 5:18 | `01_section/lecture_scripts/L08_raw_tables_setup_data_loading_copy_into.md` |
| L09 | Ethereum: Theory | 6:31 | `01_section/lecture_scripts/L09_ethereum_theory.md` |
| L10 | Git Setup | 1:42 | `01_section/lecture_scripts/L10_git_setup.md` |
| L11 | Python & dbt Package Setup | 4:30 | `01_section/lecture_scripts/L11_python_dbt_package_setup.md` |
| L12 | VS Code Setup | 3:05 | `01_section/lecture_scripts/L12_vs_code_setup.md` |
| L13 | dbt init: Project Initialization & Connection Setup | 6:59 | `01_section/lecture_scripts/L13_dbt_init_project_initialization_connection_setup.md` |
| L14 | Key Pair Authentication with Snowflake & dbt | 3:38 | `01_section/lecture_scripts/L14_key_pair_authentication_with_snowflake_dbt.md` |
| L15 | Setting Up dbt Sources | 7:44 | `01_section/lecture_scripts/L15_setting_up_dbt_sources.md` |
| L16 | Building an Enriched Transactions Model | 5:17 | `01_section/lecture_scripts/L16_building_an_enriched_transactions_model.md` |

## Section 02 — Transactions: Fields, Categorization, Activity (L17–L20)

| L# | Title | Min | File |
|---|---|---|---|
| L17 | Transaction Fields Explained | 6:50 | `02_section/lecture_scripts/L17_transaction_fields_explained.md` |
| L18 | Categorizing Ethereum Transactions | 9:32 | `02_section/lecture_scripts/L18_categorizing_ethereum_transactions.md` |
| L19 | Daily Ethereum Activity by Category | 5:54 | `02_section/lecture_scripts/L19_daily_ethereum_activity_by_category.md` |
| L20 | Daily Stablecoin Activity (USDT & USDC) | 9:24 | `02_section/lecture_scripts/L20_daily_stablecoin_activity_usdt_usdc.md` |

## Section 03 — Object Dependencies, Staging, Materializations (L21–L27)

| L# | Title | Min | File |
|---|---|---|---|
| L21 | Identifying and Verifying Raw Object Dependencies | 5:46 | `03_section/lecture_scripts/L21_identifying_and_verifying_raw_object_dependencies.md` |
| L22 | Shielding with Staging Models | 8:11 | `03_section/lecture_scripts/L22_shielding_with_staging_models.md` |
| L23 | Materialization precedence | 6:48 | `03_section/lecture_scripts/L23_materialization_precedence.md` |
| L24 | Tables vs Views | 7:45 | `03_section/lecture_scripts/L24_tables_vs_views.md` |
| L25 | Incremental Materialization | 9:26 | `03_section/lecture_scripts/L25_incremental_materialization.md` |
| L26 | Incremental Strategies | 5:39 | `03_section/lecture_scripts/L26_incremental_strategies.md` |
| L27 | Ephemeral Models | 3:57 | `03_section/lecture_scripts/L27_ephemeral_models.md` |

## Section 04 — Practice Quiz — Materializations (L28–L29)

| L# | Title | Min | File |
|---|---|---|---|
| L28 | Practice Quiz | 0:00 | `04_section/lecture_scripts/L28_practice_quiz.md` |
| L29 | Incremental model note - On Schema Change | 3:24 | `04_section/lecture_scripts/L29_incremental_model_note_on_schema_change.md` |

## Section 05 — DRY Principles, Macros (L30–L39)

| L# | Title | Min | File |
|---|---|---|---|
| L30 | DRY Principles - Intro | 1:36 | `05_section/lecture_scripts/L30_dry_principles_intro.md` |
| L31 | DRY Principles - Organizing your project | 4:56 | `05_section/lecture_scripts/L31_dry_principles_organizing_your_project.md` |
| L32 | DRY Principles - Using CTEs | 4:04 | `05_section/lecture_scripts/L32_dry_principles_using_ctes.md` |
| L33 | DRY Principles - dbt Project Configurations | 3:17 | `05_section/lecture_scripts/L33_dry_principles_dbt_project_configurations.md` |
| L34 | DRY Principles - Intro to Macros | 2:34 | `05_section/lecture_scripts/L34_dry_principles_intro_to_macros.md` |
| L35 | DRY Principles - Our First Macro | 6:46 | `05_section/lecture_scripts/L35_dry_principles_our_first_macro.md` |
| L36 | DRY Principles - Advanced Macros: Execution & Logging | 7:50 | `05_section/lecture_scripts/L36_dry_principles_advanced_macros_execution_logging.md` |
| L37 | DRY Principles - Advanced Macros: run_query() | 5:45 | `05_section/lecture_scripts/L37_dry_principles_advanced_macros_run_query.md` |
| L38 | DRY Principles - Advanced Macros: if execute & return() | 9:59 | `05_section/lecture_scripts/L38_dry_principles_advanced_macros_if_execute_return.md` |
| L39 | DRY Principles - Macros Cleanup | 0:23 | `05_section/lecture_scripts/L39_dry_principles_macros_cleanup.md` |

## Section 06 — dbt run, test, docs, seed, compile/build, DAGs (L40–L46)

| L# | Title | Min | File |
|---|---|---|---|
| L40 | Converting business logic into performant SQL queries | 3:16 | `06_section/lecture_scripts/L40_converting_business_logic_into_performant_sql_queries.md` |
| L41 | dbt run: Model Selection & Execution Flags | 7:03 | `06_section/lecture_scripts/L41_dbt_run_model_selection_execution_flags.md` |
| L42 | dbt test: Schema Tests & Data Quality | 4:35 | `06_section/lecture_scripts/L42_dbt_test_schema_tests_data_quality.md` |
| L43 | dbt docs: Documentation & Lineage | 3:29 | `06_section/lecture_scripts/L43_dbt_docs_documentation_lineage.md` |
| L44 | dbt seed: Loading & Using Static Data | 7:08 | `06_section/lecture_scripts/L44_dbt_seed_loading_using_static_data.md` |
| L45 | Additional dbt Commands: compile, ls, clean & build | 5:26 | `06_section/lecture_scripts/L45_additional_dbt_commands_compile_ls_clean_build.md` |
| L46 | Creating a logical flow of models and building clean DAGs | 8:43 | `06_section/lecture_scripts/L46_creating_a_logical_flow_of_models_and_building_clean_dags.md` |

## Section 07 — dbt_project.yml Configs (L47–L52)

| L# | Title | Min | File |
|---|---|---|---|
| L47 | Defining configurations in dbt_project.yml - Intro | 8:40 | `07_section/lecture_scripts/L47_defining_configurations_in_dbt_project_yml_intro.md` |
| L48 | Defining configurations in dbt_project.yml - YAML | 4:12 | `07_section/lecture_scripts/L48_defining_configurations_in_dbt_project_yml_yaml.md` |
| L49 | Defining configurations in dbt_project.yml - Hierarchical Configs | 3:06 | `07_section/lecture_scripts/L49_defining_configurations_in_dbt_project_yml_hierarchical_conf.md` |
| L50 | Defining configurations in dbt_project.yml - Custom Schemas | 4:55 | `07_section/lecture_scripts/L50_defining_configurations_in_dbt_project_yml_custom_schemas.md` |
| L51 | Defining configurations in dbt_project.yml - Variables | 8:38 | `07_section/lecture_scripts/L51_defining_configurations_in_dbt_project_yml_variables.md` |
| L52 | Defining configurations in dbt_project.yml - Alias config | 5:43 | `07_section/lecture_scripts/L52_defining_configurations_in_dbt_project_yml_alias_config.md` |

## Section 08 — Sources + dbt Packages (L53–L57)

| L# | Title | Min | File |
|---|---|---|---|
| L53 | Configuring Sources in dbt | 4:15 | `08_section/lecture_scripts/L53_configuring_sources_in_dbt.md` |
| L54 | Using dbt packages - CodeGen | 8:41 | `08_section/lecture_scripts/L54_using_dbt_packages_codegen.md` |
| L55 | Using dbt packages - dbt_utils & Dispatch | 8:47 | `08_section/lecture_scripts/L55_using_dbt_packages_dbt_utils_dispatch.md` |
| L56 | Using dbt packages - audit_helper & Data Comparison | 6:59 | `08_section/lecture_scripts/L56_using_dbt_packages_audit_helper_data_comparison.md` |
| L57 | Using dbt packages - Git packages, dependencies & project structure | 6:49 | `08_section/lecture_scripts/L57_using_dbt_packages_git_packages_dependencies_project_structu.md` |

## Section 09 — Git Basics + Branching + PRs + Conflicts (L58–L61)

| L# | Title | Min | File |
|---|---|---|---|
| L58 | Using Git - Basics | 8:26 | `09_section/lecture_scripts/L58_using_git_basics.md` |
| L59 | Using Git - Branching, Pull Requests & Protected Branches | 7:45 | `09_section/lecture_scripts/L59_using_git_branching_pull_requests_protected_branches.md` |
| L60 | Using Git - Merge Conflicts | 5:40 | `09_section/lecture_scripts/L60_using_git_merge_conflicts.md` |
| L61 | Using Git - Docs and Recap | 2:02 | `09_section/lecture_scripts/L61_using_git_docs_and_recap.md` |

## Section 10 — Python Models (L62–L63)

| L# | Title | Min | File |
|---|---|---|---|
| L62 | Python Models | 6:27 | `10_section/lecture_scripts/L62_python_models.md` |
| L63 | Python Models - Packages & Execution Constraints | 5:39 | `10_section/lecture_scripts/L63_python_models_packages_execution_constraints.md` |

## Section 11 — Grants (L64–L66)

| L# | Title | Min | File |
|---|---|---|---|
| L64 | Grants - Snowflake Behavior | 4:16 | `11_section/lecture_scripts/L64_grants_snowflake_behavior.md` |
| L65 | Grants - dbt grants + post-hooks | 5:57 | `11_section/lecture_scripts/L65_grants_dbt_grants_post_hooks.md` |
| L66 | Grants - Project-level grants & additive grants | 5:51 | `11_section/lecture_scripts/L66_grants_project_level_grants_additive_grants.md` |

## Section 12 — Practice Quiz — Developing dbt Models (L67–L67)

| L# | Title | Min | File |
|---|---|---|---|
| L67 | Practice Quiz - Developing dbt models | 0:00 | `12_section/lecture_scripts/L67_practice_quiz_developing_dbt_models.md` |

## Section 13 — Environments + Contracts (L68–L70)

| L# | Title | Min | File |
|---|---|---|---|
| L68 | Environments 1 | 10:20 | `13_section/lecture_scripts/L68_environments_1.md` |
| L69 | Environments 2 | 5:59 | `13_section/lecture_scripts/L69_environments_2.md` |
| L70 | Contracts - Introduction & Contract Enforcement | 5:20 | `13_section/lecture_scripts/L70_contracts_introduction_contract_enforcement.md` |

## Section 14 — Versions (L71–L72)

| L# | Title | Min | File |
|---|---|---|---|
| L71 | Versions - Setup & Latest Version View | 8:37 | `14_section/lecture_scripts/L71_versions_setup_latest_version_view.md` |
| L72 | Versions - Deprecation Dates & Warnings | 4:59 | `14_section/lecture_scripts/L72_versions_deprecation_dates_warnings.md` |

## Section 15 — Model Access (L73–L76)

| L# | Title | Min | File |
|---|---|---|---|
| L73 | Model Access - Project Structure & Fraud Domain Setup | 5:00 | `15_section/lecture_scripts/L73_model_access_project_structure_fraud_domain_setup.md` |
| L74 | Model Access - Identifying & Modeling Confirmed Fraud | 5:12 | `15_section/lecture_scripts/L74_model_access_identifying_modeling_confirmed_fraud.md` |
| L75 | Model Access - Groups & Private Models | 5:02 | `15_section/lecture_scripts/L75_model_access_groups_private_models.md` |
| L76 | Model Access - Private vs Protected Models | 4:51 | `15_section/lecture_scripts/L76_model_access_private_vs_protected_models.md` |

## Section 16 — Debugging (L77–L83)

| L# | Title | Min | File |
|---|---|---|---|
| L77 | Debugging - Understanding dbt Logs & Log Levels | 5:15 | `16_section/lecture_scripts/L77_debugging_understanding_dbt_logs_log_levels.md` |
| L78 | Debugging - Debug Flags & Log Formats | 4:30 | `16_section/lecture_scripts/L78_debugging_debug_flags_log_formats.md` |
| L79 | Runtime Errors | 3:44 | `16_section/lecture_scripts/L79_runtime_errors.md` |
| L80 | Compilation Parsing Database Errors | 8:47 | `16_section/lecture_scripts/L80_compilation_parsing_database_errors.md` |
| L81 | Troubleshooting with compiled code | 3:53 | `16_section/lecture_scripts/L81_troubleshooting_with_compiled_code.md` |
| L82 | Troubleshooting .yml compilation errors | 7:12 | `16_section/lecture_scripts/L82_troubleshooting_yml_compilation_errors.md` |
| L83 | Distinguishing dbt Core vs Data Platform Issues | 1:24 | `16_section/lecture_scripts/L83_distinguishing_dbt_core_vs_data_platform_issues.md` |

## Section 17 — State: Manifest, Run Results, Selectors, Retry (L84–L88)

| L# | Title | Min | File |
|---|---|---|---|
| L84 | Developing and implementing a fix and testing it prior to merging | 4:59 | `17_section/lecture_scripts/L84_developing_and_implementing_a_fix_and_testing_it_prior_to_me.md` |
| L85 | State Intro - Manifest and Run Results | 8:12 | `17_section/lecture_scripts/L85_state_intro_manifest_and_run_results.md` |
| L86 | State New | 6:27 | `17_section/lecture_scripts/L86_state_new.md` |
| L87 | State Selection - Result-based selectors | 3:39 | `17_section/lecture_scripts/L87_state_selection_result_based_selectors.md` |
| L88 | Combining State and Result selectors | 3:46 | `17_section/lecture_scripts/L88_combining_state_and_result_selectors.md` |

## Section 18 — Managing Data Pipelines — CI Pipelines (L89–L100)

| L# | Title | Min | File |
|---|---|---|---|
| L89 | Managing data pipelines - CI Context Intro | 9:38 | `18_section/lecture_scripts/L89_managing_data_pipelines_ci_context_intro.md` |
| L90 | Setting up our first CI pipeline - Part 1 | 7:07 | `18_section/lecture_scripts/L90_setting_up_our_first_ci_pipeline_part_1.md` |
| L91 | Setting up our first CI pipeline - Part 2 | 5:42 | `18_section/lecture_scripts/L91_setting_up_our_first_ci_pipeline_part_2.md` |
| L92 | Enhancing our pipeline - Part 1 | 7:07 | `18_section/lecture_scripts/L92_enhancing_our_pipeline_part_1.md` |
| L93 | Enhancing our pipeline - Part 2 | 3:32 | `18_section/lecture_scripts/L93_enhancing_our_pipeline_part_2.md` |
| L94 | The defer flag | 5:26 | `18_section/lecture_scripts/L94_the_defer_flag.md` |
| L95 | DBT Clone | 5:00 | `18_section/lecture_scripts/L95_dbt_clone.md` |
| L96 | To defer or to clone | 3:42 | `18_section/lecture_scripts/L96_to_defer_or_to_clone.md` |
| L97 | Slim CI - Part 1 | 7:12 | `18_section/lecture_scripts/L97_slim_ci_part_1.md` |
| L98 | Slim CI - Part 2 | 7:29 | `18_section/lecture_scripts/L98_slim_ci_part_2.md` |
| L99 | Continuous Deployment | 7:41 | `18_section/lecture_scripts/L99_continuous_deployment.md` |
| L100 | Cleanup Pipeline - Part 1 | 5:11 | `18_section/lecture_scripts/L100_cleanup_pipeline_part_1.md` |

## Section 19 — Tests, Snapshots, Microbatch, Advanced, Final Exam (L101–L131)

| L# | Title | Min | File |
|---|---|---|---|
| L101 | Cleanup Pipeline - Part 2 | 3:55 | `19_section/lecture_scripts/L101_cleanup_pipeline_part_2.md` |
| L102 | Disable Cleanup Workflow | 0:09 | `19_section/lecture_scripts/L102_disable_cleanup_workflow.md` |
| L103 | Singular data tests | 4:45 | `19_section/lecture_scripts/L103_singular_data_tests.md` |
| L104 | Generic data tests - Part 1 | 5:14 | `19_section/lecture_scripts/L104_generic_data_tests_part_1.md` |
| L105 | Generic data tests - Part 2 | 5:50 | `19_section/lecture_scripts/L105_generic_data_tests_part_2.md` |
| L106 | Out of the box data tests | 8:09 | `19_section/lecture_scripts/L106_out_of_the_box_data_tests.md` |
| L107 | Custom data tests - Overriding built-in tests | 5:03 | `19_section/lecture_scripts/L107_custom_data_tests_overriding_built_in_tests.md` |
| L108 | Tests on sources | 1:41 | `19_section/lecture_scripts/L108_tests_on_sources.md` |
| L109 | dbt Unit Tests | 10:33 | `19_section/lecture_scripts/L109_dbt_unit_tests.md` |
| L110 | Test severity and test configurations | 6:03 | `19_section/lecture_scripts/L110_test_severity_and_test_configurations.md` |
| L111 | Test selection and indirect selection | 6:35 | `19_section/lecture_scripts/L111_test_selection_and_indirect_selection.md` |
| L112 | dbt Docs | 9:20 | `19_section/lecture_scripts/L112_dbt_docs.md` |
| L113 | Exposures | 4:53 | `19_section/lecture_scripts/L113_exposures.md` |
| L114 | Source Freshness | 6:36 | `19_section/lecture_scripts/L114_source_freshness.md` |
| L115 | Tests - Advanced | 5:37 | `19_section/lecture_scripts/L115_tests_advanced.md` |
| L116 | Selectors - Advanced | 5:20 | `19_section/lecture_scripts/L116_selectors_advanced.md` |
| L117 | Namespaces - Advanced | 7:16 | `19_section/lecture_scripts/L117_namespaces_advanced.md` |
| L118 | Build - Advanced | 1:58 | `19_section/lecture_scripts/L118_build_advanced.md` |
| L119 | What's New in the May 2026 dbt Certification Exam ? | 1:55 | `19_section/lecture_scripts/L119_what_s_new_in_the_may_2026_dbt_certification_exam.md` |
| L120 | dbt show Command | 4:28 | `19_section/lecture_scripts/L120_dbt_show_command.md` |
| L121 | Snapshots: The Timestamp Strategy | 13:51 | `19_section/lecture_scripts/L121_snapshots_the_timestamp_strategy.md` |
| L122 | Snapshot Configurations | 6:27 | `19_section/lecture_scripts/L122_snapshot_configurations.md` |
| L123 | Snapshots: The Check Strategy | 3:39 | `19_section/lecture_scripts/L123_snapshots_the_check_strategy.md` |
| L124 | Incremental Models: The Microbatch Strategy | 8:59 | `19_section/lecture_scripts/L124_incremental_models_the_microbatch_strategy.md` |
| L125 | Configuring the Microbatch Strategy | 4:59 | `19_section/lecture_scripts/L125_configuring_the_microbatch_strategy.md` |
| L126 | Microbatch: Additional Configurations and Best Practices | 4:24 | `19_section/lecture_scripts/L126_microbatch_additional_configurations_and_best_practices.md` |
| L127 | Using the --sample Flag | 5:19 | `19_section/lecture_scripts/L127_using_the_sample_flag.md` |
| L128 | Final recommendations | 2:20 | `19_section/lecture_scripts/L128_final_recommendations.md` |
| L129 | Exam Cheat Sheet & Resources | 0:10 | `19_section/lecture_scripts/L129_exam_cheat_sheet_resources.md` |
| L130 | Final Test | 0:00 | `19_section/lecture_scripts/L130_final_test.md` |
| L131 | Congratulations ! Stay Connected | 0:54 | `19_section/lecture_scripts/L131_congratulations_stay_connected.md` |

---

**Total: 19 sections · 131 lectures · 11h 39m 42s of content.**

**Author:** Prem Vishnoi — pvishnoi@avilx.com
