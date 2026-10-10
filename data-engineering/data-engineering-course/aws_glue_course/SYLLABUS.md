# SYLLABUS — AWS Glue: The Complete Masterclass

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Format:** 11 sections, 81 lectures, 4h 11m total. 3 role plays (L57 in Section 8 + 2 in `assignments/`). 4 downloadable resources. 11 quizzes. 6 assignments.

This is the **authoritative lecture-to-file map**. The Udemy-published numbering (3+8+5+4+15+7+6+9+10+8+6 = 81) is mapped to local L-IDs L1–L81 below.

| Section | Lectures | Min | Title |
|---|---|---|---|
| 1 | L01–L03 | 12 | Introduction |
| 2 | L04–L11 | 21 | Glue Resources Setup Part 1 — IAM, KMS, SNS |
| 3 | L12–L16 | 16 | Glue Resources Setup Part 2 — S3, AWS CLI, CloudFormation, CloudWatch |
| 4 | L17–L20 | 6 | Creating Bucket And Uploading Data For the Course |
| 5 | L21–L35 | 58 | Glue Resources SetUp Part 3 — Glue Catalog, Crawler |
| 6 | L36–L42 | 15 | CloudFormation Templates |
| 7 | L43–L48 | 25 | First AWS Glue Pipeline Creation |
| 8 | L49–L57 | 27 | AWS Glue Job Debugging |
| 9 | L58–L67 | 28 | Glue Streaming Job |
| 10 | L68–L75 | 21 | Glue Data Quality |
| 11 | L76–L81 | 22 | Glue Data Brew |

---

## Section 1 — Introduction (L01–L03, 12 min)

| L# | Title | File |
|---|---|---|
| L01 | Course Overview | `01_introduction/lecture_scripts/L01_course_overview.md` |
| L02 | What You'll Learn | `01_introduction/lecture_scripts/L02_what_youll_learn.md` |
| L03 | Why AWS Glue (and who uses it) | `01_introduction/lecture_scripts/L03_why_aws_glue.md` |

---

## Section 2 — Glue Resources Setup Part 1: IAM, KMS, SNS (L04–L11, 21 min)

| L# | Title | File |
|---|---|---|
| L04 | Section Overview | `02_iam_kms_sns/lecture_scripts/L04_section_overview.md` |
| L05 | IAM 101 — Authentication, Authorization, Identities | `02_iam_kms_sns/lecture_scripts/L05_iam_101.md` |
| L06 | IAM Lab — Setting Up Users and User Group | `02_iam_kms_sns/lecture_scripts/L06_iam_lab_users_groups.md` |
| L07 | IAM Lab — Setting Up IAM Role | `02_iam_kms_sns/lecture_scripts/L07_iam_lab_role.md` |
| L08 | IAM 101 — Policies | `02_iam_kms_sns/lecture_scripts/L08_iam_policies.md` |
| L09 | KMS 101 + KMS Lab — Setting Up KMS Key | `02_iam_kms_sns/lecture_scripts/L09_kms_101_lab.md` |
| L10 | AWS SNS 101 | `02_iam_kms_sns/lecture_scripts/L10_sns_101.md` |
| L11 | Recap + Create `GlueJobRole` | `02_iam_kms_sns/lecture_scripts/L11_recap_create_glue_job_role.md` |

---

## Section 3 — Glue Resources Setup Part 2: S3, AWS CLI, CloudFormation, CloudWatch (L12–L16, 16 min)

| L# | Title | File |
|---|---|---|
| L12 | Section Overview | `03_s3_cli_cloudformation/lecture_scripts/L12_section_overview.md` |
| L13 | AWS S3 101 | `03_s3_cli_cloudformation/lecture_scripts/L13_s3_101.md` |
| L14 | AWS CLI 101 + Configuring with IAM User Credentials | `03_s3_cli_cloudformation/lecture_scripts/L14_cli_101_configure.md` |
| L15 | AWS CloudFormation 101 | `03_s3_cli_cloudformation/lecture_scripts/L15_cfn_101.md` |
| L16 | CloudWatch 101 (for Glue Job monitoring) | `03_s3_cli_cloudformation/lecture_scripts/L16_cloudwatch_101.md` |

---

## Section 4 — Creating Bucket And Uploading Data For the Course (L17–L20, 6 min)

| L# | Title | File |
|---|---|---|
| L17 | Section Overview | `04_s3_buckets_data/lecture_scripts/L17_section_overview.md` |
| L18 | Creating S3 Buckets (Source + Target) | `04_s3_buckets_data/lecture_scripts/L18_creating_s3_buckets.md` |
| L19 | Uploading Data to S3 Buckets (city_temperature.csv) | `04_s3_buckets_data/lecture_scripts/L19_uploading_city_temperature.md` |
| L20 | Verify the S3 Setup (Lab) | `04_s3_buckets_data/lecture_scripts/L20_verify_s3_setup.md` |

---

## Section 5 — Glue Resources SetUp Part 3: Glue Catalog, Crawler (L21–L35, 58 min)

| L# | Title | File |
|---|---|---|
| L21 | Section Overview | `05_glue_catalog_crawler/lecture_scripts/L21_section_overview.md` |
| L22 | AWS Glue Catalog 101 | `05_glue_catalog_crawler/lecture_scripts/L22_glue_catalog_101.md` |
| L23 | AWS Glue Database 101 (creating a database by hand) | `05_glue_catalog_crawler/lecture_scripts/L23_glue_database_101.md` |
| L24 | AWS Glue Table 101 (creating a table in the catalog) | `05_glue_catalog_crawler/lecture_scripts/L24_glue_table_101.md` |
| L25 | AWS Glue Crawler 101 | `05_glue_catalog_crawler/lecture_scripts/L25_glue_crawler_101.md` |
| L26 | AWS Glue Crawler Classifier 101 | `05_glue_catalog_crawler/lecture_scripts/L26_glue_crawler_classifier_101.md` |
| L27 | Crawler Lab — First Glue Crawler Creation | `05_glue_catalog_crawler/lecture_scripts/L27_crawler_lab_first.md` |
| L28 | First Glue Crawler Running | `05_glue_catalog_crawler/lecture_scripts/L28_crawler_running_first.md` |
| L29 | Crawler Lab — Second Glue Crawler Creation | `05_glue_catalog_crawler/lecture_scripts/L29_crawler_lab_second.md` |
| L30 | Crawler Lab — Third Glue Crawler Creation | `05_glue_catalog_crawler/lecture_scripts/L30_crawler_lab_third.md` |
| L31 | Crawler Lab — Fourth Glue Crawler Creation | `05_glue_catalog_crawler/lecture_scripts/L31_crawler_lab_fourth.md` |
| L32 | Crawler Lab — Fifth Glue Crawler Creation And Running | `05_glue_catalog_crawler/lecture_scripts/L32_crawler_lab_fifth.md` |
| L33 | AWS Glue Job 101 | `05_glue_catalog_crawler/lecture_scripts/L33_glue_job_101.md` |
| L34 | AWS Glue Trigger 101 (Scheduled, Conditional, On-Demand, EventBridge) | `05_glue_catalog_crawler/lecture_scripts/L34_glue_trigger_101.md` |
| L35 | AWS Glue Workflow 101 + Section Recap | `05_glue_catalog_crawler/lecture_scripts/L35_glue_workflow_101.md` |

---

## Section 6 — CloudFormation Templates (L36–L42, 15 min)

| L# | Title | File |
|---|---|---|
| L36 | Section Overview | `06_cloudformation_templates/lecture_scripts/L36_section_overview.md` |
| L37 | CloudFormation Templates 101 | `06_cloudformation_templates/lecture_scripts/L37_cfn_templates_101.md` |
| L38 | First Glue Pipeline — CFN Templates | `06_cloudformation_templates/lecture_scripts/L38_first_glue_pipeline_cfn.md` |
| L39 | Second Glue Pipeline — CFN Templates | `06_cloudformation_templates/lecture_scripts/L39_second_glue_pipeline_cfn.md` |
| L40 | Glue Job 3-4-5 — CFN Template | `06_cloudformation_templates/lecture_scripts/L40_glue_job_345_cfn.md` |
| L41 | Recap CFN Template Update | `06_cloudformation_templates/lecture_scripts/L41_recap_cfn_update.md` |
| L42 | Upload CFN Templates to S3 | `06_cloudformation_templates/lecture_scripts/L42_upload_cfn_templates_s3.md` |

---

## Section 7 — First AWS Glue Pipeline Creation (L43–L48, 25 min)

| L# | Title | File |
|---|---|---|
| L43 | Section Overview | `07_first_glue_pipeline/lecture_scripts/L43_section_overview.md` |
| L44 | Getting Ready For Glue Pipeline Creation | `07_first_glue_pipeline/lecture_scripts/L44_getting_ready.md` |
| L45 | Deploying Glue Pipeline Stack Using CloudFormation | `07_first_glue_pipeline/lecture_scripts/L45_deploying_stack.md` |
| L46 | CloudFormation Template Deployment Debugging | `07_first_glue_pipeline/lecture_scripts/L46_cfn_deployment_debug.md` |
| L47 | Analyzing Glue Job Script And Running The Job | `07_first_glue_pipeline/lecture_scripts/L47_analyzing_glue_job_script.md` |
| L48 | Going Through the Log And Verifying Job Output | `07_first_glue_pipeline/lecture_scripts/L48_going_through_log.md` |

---

## Section 8 — AWS Glue Job Debugging (L49–L57, 27 min) — incl. 1 role play (L57)

| L# | Title | File |
|---|---|---|
| L49 | Section Overview | `08_glue_job_debug/lecture_scripts/L49_section_overview.md` |
| L50 | Section Prerequisite | `08_glue_job_debug/lecture_scripts/L50_section_prereq.md` |
| L51 | Fix Error Retrieving The Script | `08_glue_job_debug/lecture_scripts/L51_fix_script_retrieval.md` |
| L52 | Fix Launch Error And Glue Argument Error | `08_glue_job_debug/lecture_scripts/L52_fix_launch_arg_error.md` |
| L53 | Fix Resource Policy Error — Error Reading From Source Bucket | `08_glue_job_debug/lecture_scripts/L53_fix_resource_policy.md` |
| L54 | Fix Identity Policy Error — Error Reading The Key | `08_glue_job_debug/lecture_scripts/L54_fix_identity_policy.md` |
| L55 | Workflow Running GlueJob2 | `08_glue_job_debug/lecture_scripts/L55_workflow_running_gluejob2.md` |
| L56 | Recap | `08_glue_job_debug/lecture_scripts/L56_recap.md` |
| L57 | **Role Play — Diagnose Glue Job Failure: Role/Trust Misconfig** | `08_glue_job_debug/lecture_scripts/L57_role_play_trust_misconfig.md` |

The Udemy syllabus for Section 8 lists 9 lectures. The "3 role plays" promise in the course description maps to L57 (one role play in this section) plus 2 stand-alone role plays referenced in the assignments (`assignments/`). See also `quizzes/section_8.md` for the role-play synthesis questions.

---

## Section 9 — Glue Streaming Job (L58–L67, 28 min)

| L# | Title | File |
|---|---|---|
| L58 | Section Overview | `09_glue_streaming/lecture_scripts/L58_section_overview.md` |
| L59 | Getting Ready For Glue Streaming Pipeline | `09_glue_streaming/lecture_scripts/L59_getting_ready_streaming.md` |
| L60 | Deploying Glue Streaming Job Infrastructure | `09_glue_streaming/lecture_scripts/L60_deploying_streaming_infra.md` |
| L61 | Lab — Creating Python Shell Glue Job For Stream Generation | `09_glue_streaming/lecture_scripts/L61_python_shell_generator.md` |
| L62 | Lab — Creating Glue Streaming Loading Job | `09_glue_streaming/lecture_scripts/L62_streaming_loading_job.md` |
| L63 | Lab — Creating Glue Streaming Transforming Job | `09_glue_streaming/lecture_scripts/L63_streaming_transforming_job.md` |
| L64 | Recap Before Running All Three Glue Streaming Jobs | `09_glue_streaming/lecture_scripts/L64_recap_before_running.md` |
| L65 | Running Glue Streaming Generator Job | `09_glue_streaming/lecture_scripts/L65_running_generator.md` |
| L66 | Running Glue Streaming Transformation Job | `09_glue_streaming/lecture_scripts/L66_running_transformation.md` |
| L67 | Section Recap | `09_glue_streaming/lecture_scripts/L67_section_recap.md` |

---

## Section 10 — Glue Data Quality (L68–L75, 21 min)

| L# | Title | File |
|---|---|---|
| L68 | Section Overview | `10_glue_data_quality/lecture_scripts/L68_section_overview.md` |
| L69 | Data Quality 101 | `10_glue_data_quality/lecture_scripts/L69_data_quality_101.md` |
| L70 | Setting Up Data Quality Rule Set | `10_glue_data_quality/lecture_scripts/L70_dq_rule_set.md` |
| L71 | Glue Job With Data Quality Check | `10_glue_data_quality/lecture_scripts/L71_glue_job_dq_check.md` |
| L72 | Running the Glue Job | `10_glue_data_quality/lecture_scripts/L72_running_dq_job.md` |
| L73 | Setting Up Glue Data Quality CloudWatch Metrics | `10_glue_data_quality/lecture_scripts/L73_dq_cloudwatch.md` |
| L74 | Receiving Alerts for Data Quality Issues | `10_glue_data_quality/lecture_scripts/L74_receiving_alerts.md` |
| L75 | Section Recap | `10_glue_data_quality/lecture_scripts/L75_section_recap.md` |

---

## Section 11 — Glue Data Brew (L76–L81, 22 min)

| L# | Title | File |
|---|---|---|
| L76 | Section Overview | `11_glue_databrew/lecture_scripts/L76_section_overview.md` |
| L77 | DataBrew 101 | `11_glue_databrew/lecture_scripts/L77_databrew_101.md` |
| L78 | Create DataSource and Profile Data | `11_glue_databrew/lecture_scripts/L78_create_datasource_profile.md` |
| L79 | Create Project and Review Data Profile Output | `11_glue_databrew/lecture_scripts/L79_create_project_review_profile.md` |
| L80 | Create and Publish Recipe | `11_glue_databrew/lecture_scripts/L80_create_publish_recipe.md` |
| L81 | Create Job by Using Published Recipe (Lab) | `11_glue_databrew/lecture_scripts/L81_create_job_published_recipe.md` |

---

## Totals

- **Total lectures:** 81 (L01–L81)
- **Total duration:** 4h 11m
- **Total role plays:** 1 in Section 8 (L57) + 2 referenced in assignments = 3 (matches the course description)
- **Total quizzes:** 11 (`quizzes/section_1.md` … `quizzes/section_11.md`)
- **Total downloadable resources:** 4 (in `downloads/`)
- **Total assignments:** 6 (in `assignments/`)
