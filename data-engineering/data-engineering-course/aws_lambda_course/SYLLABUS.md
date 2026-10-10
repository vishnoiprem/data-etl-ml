# SYLLABUS — AWS Lambda, Python (Boto3) & Serverless — Beginner to Advanced

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Format:** **16 sections**, **81 lectures**, **~9h 11m** total. 3 hands-on enterprise use cases (banking, serverless CRUD, Bedrock GenAI). 16 quizzes (one per section). 4 downloadable resources.
> **Source:** Udemy-published curriculum "AWS Lambda, Python(Boto3) & Serverless- Beginner to Advanced" (October 2026 edition).

This is the **authoritative lecture-to-file map**. The Udemy lecture order is preserved exactly as L01–L81 below. Section folders are numbered to match the Udemy course sections.

| Section | Lectures | Min | Title |
|---|---|---|---|
| 1 | L01–L02 | 6 | Introduction |
| 2 | L03–L08 | 26 | AWS Lambda — Basic Concepts (Part 1) |
| 3 | L09–L10 | 23 | Python Basics Refresher |
| 4 | L11–L18 | 76 | AWS Lambda — Create S3, EC2, DynamoDB Resources |
| 5 | L19–L22 | 15 | AWS Lambda — Basic Concepts (Part 2): Invocation Model & Limits |
| 6 | L23–L24 | 20 | Enterprise Use Case 1 — S3, Lambda, DynamoDB |
| 7 | L25–L29 | 30 | API Gateway Overview |
| 8 | L30–L35 | 46 | Enterprise Use Case 2 — API Gateway, Lambda, S3 |
| 9 | L36–L39 | 44 | API Security — Lambda Authorizer & Cognito Authorizer |
| 10 | L40–L46 | 40 | Generative AI — AWS Bedrock (Cohere) End-to-End |
| 11 | L47–L59 | 60 | AWS Lambda — Advanced Concepts |
| 12 | L71–L77 | 45 | AWS CDK v2 — Implementing Serverless Use Case 2 |
| 13 | L60–L70 | 73 | AWS CloudFormation — Implementing Serverless Use Case 2 |
| 14 | L78–L81 | 32 | Python Basics — Appendix (PyCharm, Print, Variables, Data Types, Functions) |
| 15 | (assets) | – | Diagrams, Mermaid, Architecture |
| 16 | (downloads) | – | PDF/zip resources |

**Total: 81 lectures, ~9h 11m, 3 enterprise use cases, 16 quizzes, 4 downloads.**

> **Note on section ordering:** Sections 12 (CDK) and 13 (CloudFormation) ship in the
> Udemy course *after* section 11 (Advanced), so the L-IDs jump (L60–L70 CFN
> interleaves with L71–L77 CDK). To avoid local folder-number confusion, section
> 13's CFN lectures map to `13_cloudformation_serverless/lecture_scripts/` even
> though their L-IDs are 60–70.

---

## Section 1 — Introduction (L01–L02, 6 min)

| L# | Title | Min | File |
|---|---|---|---|
| L01 | Must Watch — Course Introduction and Download Content Slides | 4:09 | `01_introduction/lecture_scripts/L01_course_intro.md` |
| L02 | Course Pre-Requisites | 2:19 | `01_introduction/lecture_scripts/L02_prerequisites.md` |

---

## Section 2 — AWS Lambda Basic Concepts (Part 1) (L03–L08, ~26 min)

| L# | Title | Min | File |
|---|---|---|---|
| L03 | AWS Lambda — Basic Concepts Part 1 — Section Overview | 0:22 | `02_lambda_basic_concepts/lecture_scripts/L03_section_overview.md` |
| L04 | Evolution from Physical Servers to AWS Lambda | 5:22 | `02_lambda_basic_concepts/lecture_scripts/L04_evolution.md` |
| L05 | What is AWS Lambda and Use Cases | 5:25 | `02_lambda_basic_concepts/lecture_scripts/L05_what_is_lambda.md` |
| L06 | Lambda Console Walkthrough | 10:38 | `02_lambda_basic_concepts/lecture_scripts/L06_console_walkthrough.md` |
| L07 | Lambda Execution Role | 4:39 | `02_lambda_basic_concepts/lecture_scripts/L07_execution_role.md` |
| L08 | AWS Lambda — Conceptual Understanding Review | — | `02_lambda_basic_concepts/lecture_scripts/L08_conceptual_review.md` |

---

## Section 3 — Python Basics Refresher (L09–L10, 23 min)

| L# | Title | Min | File |
|---|---|---|---|
| L09 | Python Basics Refresher — Part 1 | 8:00 | `03_python_basics/lecture_scripts/L09_python_basics_pt1.md` |
| L10 | Python Basics Refresher — Part 2 | 15:11 | `03_python_basics/lecture_scripts/L10_python_basics_pt2.md` |

---

## Section 4 — AWS Lambda with S3, EC2, DynamoDB (L11–L18, 76 min)

| L# | Title | Min | File |
|---|---|---|---|
| L11 | Section Overview | 1:18 | `04_lambda_with_aws_resources/lecture_scripts/L11_section_overview.md` |
| L12 | AWS Lambda Basics — Boto3, Client and Resource, Lambda function handler | 9:06 | `04_lambda_with_aws_resources/lecture_scripts/L12_boto3_handler.md` |
| L13 | Create S3 Bucket with AWS Lambda and Boto3 | 15:00 | `04_lambda_with_aws_resources/lecture_scripts/L13_create_s3_bucket.md` |
| L14 | Delete S3 Bucket with AWS Lambda and Boto3 | 6:07 | `04_lambda_with_aws_resources/lecture_scripts/L14_delete_s3_bucket.md` |
| L15 | List S3 Bucket with AWS Lambda and Boto3 | 8:39 | `04_lambda_with_aws_resources/lecture_scripts/L15_list_s3_buckets.md` |
| L16 | AWS Lambda with EC2 (Create EC2, Start EC2 and Stop EC2) | 12:59 | `04_lambda_with_aws_resources/lecture_scripts/L16_lambda_with_ec2.md` |
| L17 | AWS Lambda Automation Use Case — EC2, Lambda and EventBridge | 12:29 | `04_lambda_with_aws_resources/lecture_scripts/L17_lambda_eventbridge_ec2.md` |
| L18 | AWS Lambda with DynamoDB (Create Table and Put Items) | 10:52 | `04_lambda_with_aws_resources/lecture_scripts/L18_lambda_with_dynamodb.md` |

---

## Section 5 — AWS Lambda Basic Concepts (Part 2) (L19–L22, 15 min)

| L# | Title | Min | File |
|---|---|---|---|
| L19 | AWS Lambda — Basic Concepts Part 2 — Section Overview | 0:32 | `05_lambda_basic_concepts_pt2/lecture_scripts/L19_section_overview.md` |
| L20 | AWS Lambda Invocation Model — Theory | 3:33 | `05_lambda_basic_concepts_pt2/lecture_scripts/L20_invocation_model_theory.md` |
| L21 | AWS Lambda Invocation Model — Hands On | 7:16 | `05_lambda_basic_concepts_pt2/lecture_scripts/L21_invocation_model_hands_on.md` |
| L22 | Lambda Limits — Timeout | 4:06 | `05_lambda_basic_concepts_pt2/lecture_scripts/L22_lambda_limits_timeout.md` |

---

## Section 6 — Enterprise Use Case 1: S3, Lambda, DynamoDB (L23–L24, 20 min)

| L# | Title | Min | File |
|---|---|---|---|
| L23 | Enterprise Use Case using S3, AWS Lambda and DynamoDB — Part 1 | 11:24 | `06_usecase1_s3_lambda_dynamodb/lecture_scripts/L23_usecase1_pt1.md` |
| L24 | Enterprise Use Case using S3, AWS Lambda and DynamoDB — Part 2 | 8:27 | `06_usecase1_s3_lambda_dynamodb/lecture_scripts/L24_usecase1_pt2.md` |

---

## Section 7 — API Gateway Overview (L25–L29, 30 min)

| L# | Title | Min | File |
|---|---|---|---|
| L25 | API Gateway — Overview, API Types, API Endpoint Types | 7:08 | `07_apigw_overview/lecture_scripts/L25_apigw_overview.md` |
| L26 | API Gateway — Resources, Methods and Integration Types | 5:45 | `07_apigw_overview/lecture_scripts/L26_resources_methods_integrations.md` |
| L27 | API Gateway — Deployment, API Stages, API Keys and Usage Plans | 3:24 | `07_apigw_overview/lecture_scripts/L27_deployment_stages_keys.md` |
| L28 | API Gateway — Authentication and Authorization Methods | 6:48 | `07_apigw_overview/lecture_scripts/L28_auth_methods.md` |
| L29 | API Gateway — Private APIs and Private Integration | 7:04 | `07_apigw_overview/lecture_scripts/L29_private_apis.md` |

---

## Section 8 — Enterprise Use Case 2: API Gateway, Lambda, S3 (L30–L35, 46 min)

| L# | Title | Min | File |
|---|---|---|---|
| L30 | Serverless Enterprise Use Case 2 — Architecture (API Gateway, AWS Lambda and S3) | 1:01 | `08_usecase2_apigw_lambda_s3/lecture_scripts/L30_usecase2_architecture.md` |
| L31 | S3, Lambda and API Gateway — Part 1 | 12:29 | `08_usecase2_apigw_lambda_s3/lecture_scripts/L31_s3_lambda_apigw_pt1.md` |
| L31a | Enterprise Use Case using API Gateway, AWS Lambda and S3 — Part 3 | 9:43 | `08_usecase2_apigw_lambda_s3/lecture_scripts/L31a_usecase2_pt3.md` |
| L32 | S3, Lambda and API Gateway with Query String Parameters — Part 2 | 9:43 | `08_usecase2_apigw_lambda_s3/lecture_scripts/L32_query_string_params_pt2.md` |
| L33 | API Keys and Usage Plan — Theory | 4:10 | `08_usecase2_apigw_lambda_s3/lecture_scripts/L33_api_keys_theory.md` |
| L34 | API Keys and Usage Plan — Hands On | 7:56 | `08_usecase2_apigw_lambda_s3/lecture_scripts/L34_api_keys_hands_on.md` |
| L35 | Agentic AI Architect Roadmap on AWS: Skills You Need to Learn in 2026 (Optional) | 10:10 | `08_usecase2_apigw_lambda_s3/lecture_scripts/L35_agentic_ai_roadmap.md` |

---

## Section 9 — API Security: Lambda Authorizer & Cognito Authorizer (L36–L39, 44 min)

| L# | Title | Min | File |
|---|---|---|---|
| L36 | Securing APIs using AWS Lambda Authorizer — Theory | 3:30 | `09_api_security_lambda_cognito_auth/lecture_scripts/L36_lambda_authorizer_theory.md` |
| L37 | Securing APIs using AWS Lambda Authorizer — Hands On | 23:46 | `09_api_security_lambda_cognito_auth/lecture_scripts/L37_lambda_authorizer_hands_on.md` |
| L38 | Securing APIs using AWS Cognito Authorizer — Theory | 2:42 | `09_api_security_lambda_cognito_auth/lecture_scripts/L38_cognito_authorizer_theory.md` |
| L39 | Securing APIs using AWS Cognito Authorizer — Hands On | 14:11 | `09_api_security_lambda_cognito_auth/lecture_scripts/L39_cognito_authorizer_hands_on.md` |

---

## Section 10 — Generative AI: AWS Bedrock (Cohere) End-to-End (L40–L46, 40 min)

| L# | Title | Min | File |
|---|---|---|---|
| L40 | Section Overview | 0:26 | `10_generative_ai_bedrock/lecture_scripts/L40_section_overview.md` |
| L41 | Generative AI — Use Case and Architecture | 4:01 | `10_generative_ai_bedrock/lecture_scripts/L41_use_case_architecture.md` |
| L42 | Generative AI — AWS Bedrock Overview | 2:24 | `10_generative_ai_bedrock/lecture_scripts/L42_bedrock_overview.md` |
| L43 | Generative AI — AWS Lambda Prerequisites | 5:50 | `10_generative_ai_bedrock/lecture_scripts/L43_lambda_prereqs.md` |
| L44 | Generative AI — Write AWS Lambda Function to access Bedrock | 20:36 | `10_generative_ai_bedrock/lecture_scripts/L44_lambda_bedrock.md` |
| L45 | Generative AI — Create REST API using API Gateway to access Bedrock | 5:34 | `10_generative_ai_bedrock/lecture_scripts/L45_apigw_bedrock.md` |
| L46 | Generative AI — End to End Demo | 1:13 | `10_generative_ai_bedrock/lecture_scripts/L46_e2e_demo.md` |

---

## Section 11 — AWS Lambda Advanced Concepts (L47–L59, 60 min)

| L# | Title | Min | File |
|---|---|---|---|
| L47 | AWS Lambda — Advanced Concepts — Section Overview | 0:29 | `11_lambda_advanced_concepts/lecture_scripts/L47_section_overview.md` |
| L48 | Lambda Execution and Concurrency | 8:24 | `11_lambda_advanced_concepts/lecture_scripts/L48_concurrency.md` |
| L49 | Lambda — Reserved and Provisioned Concurrency | 5:32 | `11_lambda_advanced_concepts/lecture_scripts/L49_reserved_provisioned_concurrency.md` |
| L50 | Lambda Limits — Memory | 4:22 | `11_lambda_advanced_concepts/lecture_scripts/L50_memory_limits.md` |
| L51 | Lambda — VPC Networking Configuration | 5:44 | `11_lambda_advanced_concepts/lecture_scripts/L51_vpc_networking.md` |
| L52 | Lambda — VPC Networking Configuration Hands On | 5:34 | `11_lambda_advanced_concepts/lecture_scripts/L52_vpc_networking_hands_on.md` |
| L53 | Lambda Monitoring — CloudWatch Metrics | 5:55 | `11_lambda_advanced_concepts/lecture_scripts/L53_cw_metrics.md` |
| L54 | Lambda Monitoring — CloudWatch Metrics — Hands On | 6:17 | `11_lambda_advanced_concepts/lecture_scripts/L54_cw_metrics_hands_on.md` |
| L55 | Lambda Monitoring — CloudWatch Logs | 2:17 | `11_lambda_advanced_concepts/lecture_scripts/L55_cw_logs.md` |
| L56 | Lambda Monitoring — CloudWatch Logs — Hands On | 5:27 | `11_lambda_advanced_concepts/lecture_scripts/L56_cw_logs_hands_on.md` |
| L57 | Lambda Versions | 5:44 | `11_lambda_advanced_concepts/lecture_scripts/L57_versions.md` |
| L58 | Lambda Aliases | 5:25 | `11_lambda_advanced_concepts/lecture_scripts/L58_aliases.md` |
| L59 | Lambda — Environment Variables | 4:42 | `11_lambda_advanced_concepts/lecture_scripts/L59_env_vars.md` |

---

## Section 12 — AWS CDK v2 (Infrastructure as Code) (L71–L77, 45 min)

> **Note:** The Udemy course places CDK after the Lambda Advanced section but
> before CloudFormation in lecture-numbering. To keep the local folder order
> matching the course narrative, CDK lives in folder 12 and CFN in 13.

| L# | Title | Min | File |
|---|---|---|---|
| L71 | (Optional Lecture) Introduction to AWS Cloud Development Kit (CDK) | 7:23 | `12_cdk_v2_serverless/lecture_scripts/L71_cdk_intro.md` |
| L72 | AWS CDK v2 — Pre-requisites | 9:27 | `12_cdk_v2_serverless/lecture_scripts/L72_cdk_prereqs.md` |
| L73 | Implementing Serverless Use Case 2 using AWS CDK v2 | 0:39 | `12_cdk_v2_serverless/lecture_scripts/L73_cdk_implementing_usecase2.md` |
| L74 | AWS CDK — Create S3 bucket using AWS CDK v2 | 11:22 | `12_cdk_v2_serverless/lecture_scripts/L74_cdk_s3.md` |
| L75 | AWS CDK — Create IAM Role using AWS CDK v2 | 6:56 | `12_cdk_v2_serverless/lecture_scripts/L75_cdk_iam_role.md` |
| L76 | AWS CDK — Create Lambda using AWS CDK v2 | 8:57 | `12_cdk_v2_serverless/lecture_scripts/L76_cdk_lambda.md` |
| L77 | AWS CDK — Create API Gateway using AWS CDK v2 | 7:53 | `12_cdk_v2_serverless/lecture_scripts/L77_cdk_apigw.md` |

---

## Section 13 — AWS CloudFormation (Infrastructure as Code) (L60–L70, 73 min)

> **Note:** The Udemy course places CloudFormation *after* the Advanced section
> (lecture 60) and *before* CDK (lecture 71) in the published numbering. We
> keep L60–L70 together because they form one cohesive CFN module.

| L# | Title | Min | File |
|---|---|---|---|
| L60 | Optional — AWS CloudFormation Basics | 2:29 | `13_cloudformation_serverless/lecture_scripts/L60_cfn_basics.md` |
| L61 | AWS CloudFormation — Serverless Architecture (API Gateway, AWS Lambda and S3) | 2:16 | `13_cloudformation_serverless/lecture_scripts/L61_cfn_architecture.md` |
| L62 | AWS CloudFormation — S3 Bucket | 6:25 | `13_cloudformation_serverless/lecture_scripts/L62_cfn_s3.md` |
| L63 | AWS CloudFormation — Lambda Execution Role | 6:09 | `13_cloudformation_serverless/lecture_scripts/L63_cfn_lambda_role.md` |
| L64 | AWS CloudFormation — AWS Lambda | 14:02 | `13_cloudformation_serverless/lecture_scripts/L64_cfn_lambda.md` |
| L65 | AWS CloudFormation — REST API and API Resources | 7:17 | `13_cloudformation_serverless/lecture_scripts/L65_cfn_rest_api.md` |
| L66 | AWS CloudFormation — API Method and API Deployment | 14:35 | `13_cloudformation_serverless/lecture_scripts/L66_cfn_method_deploy.md` |
| L67 | AWS CloudFormation — Lambda Invoke Permission | 4:29 | `13_cloudformation_serverless/lecture_scripts/L67_cfn_invoke_permission.md` |
| L68 | AWS CloudFormation — End to End Demo | 1:10 | `13_cloudformation_serverless/lecture_scripts/L68_cfn_e2e_demo.md` |
| L69 | AWS CloudFormation — End to End with Parameters Section | 8:55 | `13_cloudformation_serverless/lecture_scripts/L69_cfn_parameters.md` |
| L70 | AWS CloudFormation — End to End with Metadata and Parameters Section | 4:34 | `13_cloudformation_serverless/lecture_scripts/L70_cfn_metadata_params.md` |

---

## Section 14 — Python Basics Appendix (L78–L81, 32 min)

> **Note:** The Udemy course places this Python Basics appendix *after* CDK
> (lecture 78). It's a deeper dive than section 3's refresher and is intended
> for absolute beginners.

| L# | Title | Min | File |
|---|---|---|---|
| L78 | Python Basics — Section Overview | 0:56 | `14_python_basics_appx/lecture_scripts/L78_section_overview.md` |
| L79 | Python Basics – 1 : PyCharm, Print Function, Variables, Format, User Input | 9:11 | `14_python_basics_appx/lecture_scripts/L79_python_basics_1.md` |
| L80 | Python Basics – 2 : Data Types Intro, For Loops and Data Type – Dictionary | 13:03 | `14_python_basics_appx/lecture_scripts/L80_python_basics_2.md` |
| L81 | Python Basics – 3 : Data Type – List and Functions | 8:58 | `14_python_basics_appx/lecture_scripts/L81_python_basics_3.md` |

---

## Quizzes (16 — one per section)

| # | Section | File |
|---|---|---|
| 1 | Introduction | `quizzes/section_1.md` |
| 2 | Lambda Basic Concepts Pt 1 | `quizzes/section_2.md` |
| 3 | Python Refresher | `quizzes/section_3.md` |
| 4 | Lambda with S3/EC2/DynamoDB | `quizzes/section_4.md` |
| 5 | Lambda Basic Concepts Pt 2 | `quizzes/section_5.md` |
| 6 | Use Case 1 | `quizzes/section_6.md` |
| 7 | API Gateway Overview | `quizzes/section_7.md` |
| 8 | Use Case 2 | `quizzes/section_8.md` |
| 9 | API Security | `quizzes/section_9.md` |
| 10 | Generative AI Bedrock | `quizzes/section_10.md` |
| 11 | Lambda Advanced | `quizzes/section_11.md` |
| 12 | CDK v2 | `quizzes/section_12.md` |
| 13 | CloudFormation | `quizzes/section_13.md` |
| 14 | Python Basics Appendix | `quizzes/section_14.md` |

---

## Downloadable resources (4)

| # | File |
|---|---|
| 1 | `downloads/lambda_cheat_sheet.pdf` |
| 2 | `downloads/boto3_patterns_cheat_sheet.pdf` |
| 3 | `downloads/cfn_serverless_template_pack.zip` |
| 4 | `downloads/cdk_serverless_project_pack.zip` |
