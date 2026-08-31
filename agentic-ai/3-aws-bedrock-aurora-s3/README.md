
How I Built a RAG Chatbot Using LangChain and Amazon Bedrock 
In this Cloud Lab, you'll learn to create a RAG chatbot using Bedrock Knowledge Bases and base models. You'll also explore utilizing these resources to build a LangChain chatbot.
Learning Objectives
An understanding of the Bedrock Knowledge Bases
Hands-on experience using Bedrock base models in LangChain applications
Practical expertise in in using Aurora Serverless with Bedrock Knowledge Bases

---

Bedrock
Aurora
S3

Cloud Lab Overview
LangChain allows us to easily create LLM applications using a simple chain-like structure. We can integrate the capabilities of LangChain with AWS Bedrock Knowledge Bases and foundational models to create chatbots.
In this Cloud Lab, you'll learn how to build a Retrieval-Augmented Generation (RAG) chatbot using LangChain and Amazon Bedrock. You'll start by setting up an Amazon Bedrock Knowledge Base with an Aurora Serverless instance as its vector store. Also, you'll create an S3 bucket to store the source files for the knowledge base. The knowledge base will access the S3 bucket through an IAM role. Then, you'll use LangChain to create a retriever and generator chain. You'll use the knowledge base as the retriever and the Anthropic Claude model as the generator. Finally, you'll bring your application to life with a Streamlit frontend to test your RAG model.
By the end of this Cloud Lab, you'll be well-equipped to use Bedrock Knowledge Bases and base models in your AI applications. The architecture diagram shows the infrastructure you'll build in this Cloud Lab:
Why RAG chatbots are the most practical kind of "AI assistant"
Most real-world chatbots fail for one simple reason: they don't have reliable access to your knowledge. A general-purpose model can write fluent answers, but it can't be trusted to know your product docs, internal policies, or the latest information your users need.
Retrieval-augmented generation (RAG) addresses this issue by incorporating a retrieval step prior to generation. The chatbot pulls relevant chunks from your documents and then uses those chunks as grounding context for the model's response. The result is an assistant that can sound natural while staying anchored to your content.
Where LangChain fits in a RAG system
LangChain is commonly used as an orchestration layer. It helps you wire together the moving pieces of a RAG pipeline:
Document loaders and preprocessing

Chunking strategies

Embeddings generation

Vector search and retrieval

Prompt templates and response formatting

Memory and conversational patterns (when appropriate)

The advantage is speed and clarity: you can prototype and iterate on your pipeline without rewriting glue code every time you change a component.
Why Amazon Bedrock is a good model layer for RAG
Amazon Bedrock provides managed access to foundation models and (depending on your setup) embeddings. In a RAG chatbot, Bedrock typically supplies the generation step, turning the user question and retrieved context into a final answer.
When teams build on AWS, the appeal is that Bedrock integrates naturally with the rest of the stack you already use (storage, serverless, IAM, observability). That makes it easier to move from "prototype" to "something you can actually operate."
The key design decisions that shape chatbot quality
A RAG chatbot's quality usually depends less on the model and more on the retrieval design choices:
Chunking and document structure: Good chunk boundaries (based on headings/sections) often outperform arbitrary fixed-size splits.

Retrieval strategy: Semantic retrieval is powerful, but hybrid retrieval (semantic + keyword) can be even better for technical documentation.

Metadata filtering: If you have multiple products, versions, or audiences, filters reduce irrelevant results and improve precision.

Prompt discipline: The prompt should explicitly instruct the model to rely on the provided context and avoid guessing. This is one of the highest ROI "guardrails" you can add.

Fallback behavior: Define what happens when retrieval is weak: ask a clarifying question, respond with "I don't know," or route to a human/help article.

How to evaluate a RAG chatbot before shipping it
A practical evaluation approach includes:
A test set of real user questions.

Checks for retrieval relevance (did it fetch the right chunks?).

Checks for faithfulness (did the answer stick to sources?).

Latency and cost monitoring (RAG can get expensive if you retrieve too much).

Safety and Privacy Review (What Data Can the Bot Access?).

The goal isn't perfection, it's predictable behavior under the queries your users will actually ask.
1.Introduction
Getting Started
2.Set Up the Knowledge Base
Set Up Aurora Serverless
Create an S3 Bucket
Create a Knowledge Base
3.Deploy the LangChain Application
Create a LangChain Application
Create a Streamlit Application
4.Conclusion
Clean Up
Wrap Up

Getting Started
Amazon Bedrock provides base models that can easily be integrated into our environment. It offers multiple models, such as Anthropic, Titan, and more. Additionally, it allows us to create knowledge bases to store vector embeddings. These features, in combination with a comprehensive framework such as LangChain, can help deploy LLMs in a few easy steps.
In this lab, we'll create a chatbot to query the differences between Amazon SageMaker and Bedrock. Our data source will be a PDF file discussing these differences. We'll utilize LangChain's generator retriever architecture to design the chatbot effectively.

We'll create a knowledge base with an S3 bucket as the data source and configure the Aurora Serverless instance to store the vector embeddings. Next, we'll code a chatbot with LangChain. The chatbot will use the knowledge base as the retriever and the Anthropic Claude model as the generator. Finally, we'll build a frontend using Streamlit and query our RAG chatbot.
General instructions
Here are some general guidelines that will help you complete this lab:
Before starting this lab, ensure that you're working within the us-east-1 region, as access to resources outside of this region has been restricted for this lab. On the AWS Management Console, click the region drop-down menu at the top-right corner next to your username and select the "US East (N. Virginia)" option.

Using the same resource names as suggested in the lab is essential. For instance, if you are instructed to name a function as my_function, choosing any other name for the function may not be possible.

There are limited permissions to attempt this lab, and some console pages may display insufficient privilege error messages. These can be safely ignored.

Now that the instructions have been understood let's get started.

Set Up Aurora Serverless
Aurora Serverless is an on-demand auto-scaling database service provided by Amazon Aurora. Amazon Aurora is a relational database management service (RDBMS) provided by AWS that supports MySQL and PostgreSQL. Amazon Bedrock allows us to use Aurora Serverless PostgreSQL as the vector store.
In this task, we'll create an Aurora Serverless database as the vector store for our knowledge base. The provisioned infrastructure is shown below:

Create a database
Follow these steps to create an Aurora Serverless database:
Search "aurora" on the AWS Management Console and select "Aurora and RDS" to open the RDS dashboard.

Click the "Create database" button. Select "Full configuration" from the database creation method.

From the engine options, select "Aurora (PostgreSQL Compatible)."

In the "Templates" section, choose "Dev/Test."

In the "Cluster scalability type," choose the "Aurora serverless" option. Ensure that "Minimum capacity (ACUs)" is set to 1 and "Maximum ACUs" in "Capacity range" is set to 2.

Under the "Settings" section:

Select "Aurora PostgreSQL (Compatible with PostgreSQL 17.7)" as the engine version.

Set the "DB cluster identifier" as vector-store. This identifier is used in the cluster's endpoint.

In the "Credentials Settings," keep the default "Master username" as postgres. Select "Managed in AWS Secrets Manager - most secure." This will automatically create a new secret for our Aurora cluster.

In the "Connectivity" section, check the "Enable the RDS Data API" checkbox. This will allow us to run queries on the database using the query editor.

In "Monitoring," uncheck "Enable collecting detailed per-query and database counter metrics." Also, expand "Additional monitoring settings" and uncheck "Enable Enhanced monitoring."

Expand the "Additional configuration" section and enter "Initial database name" as VectorDatabase.

Select "AWS owned KMS key (SSE-RDS)" for "Encryption key" in the "Encryption" subsection.

Keep the rest of the settings to the default; scroll down and click "Create database."

Note: It will take 5–10 minutes for the cluster and instance to become available. Meanwhile, we can copy the ARN of our secret.

Get the ARN of the secret
Aurora has automatically created a secret to manage access to our cluster. We need the secret to connect to the cluster. Follow the steps below to get the ARN of our secret:
Search "Secret" on the AWS Management Console and select "Secrets Manager" to open the Secret Manager dashboard.

Here, open the secret with the name starting with rds!cluster. In the "Secret details" section, copy the ARN of the secret and keep it somewhere, as we'll be using it to connect to the Aurora cluster.

In the "Overview" tab, click the "Retrieve secret value" button in the "Secret value" section to retrieve the username and password.

Copy the password and save it somewhere safe.

Now, switch back to the RDS console by searching for "RDS" in the AWS Management Console. Click "Databases" from the sidebar menu to open the cluster. If the status of the vector-store is set to "available," follow the steps given below to copy the ARN of the cluster, as we'll be needing it while creating the Bedrock Knowledge Base:
Click the cluster name to open it and switch to the "Configuration" tab.

Copy the "Amazon Resource Name (ARN)" of the cluster and save it somewhere safe.

Connect to the Database
Now, we'll connect to the database to install pgvector and set up database objects and privileges. Follow the steps below to connect to the database:
Select "Query Editor" from the sidebar menu to open the "Connect to database" pop-up.

Select vector-store as the "Database instance or cluster."

Select "Connect with Secrets Manager ARN" as the "Database username."

In the field "Secrets manager ARN," paste the ARN of the secrets manager we copied in the previous step.

Enter VectorDatabase as the name of the database and click "Connect to database."

This will open up the Query editor. Try clicking the "Run" button to run the SQL command that lists our cluster's databases.
Copy and paste the following command to set up pgvector:
CREATE EXTENSION IF NOT EXISTS vector;
SELECT extversion FROM pg_extension WHERE extname='vector';
Now, let's set up the database and table for our vector store. We'll also create a new role and grant it access to the database.
CREATE SCHEMA bedrock_integration;
CREATE ROLE bedrock_user WITH PASSWORD '<SECRET-PASSWORD>' LOGIN;
GRANT ALL ON SCHEMA bedrock_integration to bedrock_user;
CREATE TABLE bedrock_integration.bedrock_kb (id uuid PRIMARY KEY, embedding vector(1024), chunks text, metadata json);
CREATE INDEX ON bedrock_integration.bedrock_kb USING gin (to_tsvector('simple', chunks));
CREATE INDEX ON bedrock_integration.bedrock_kb USING hnsw (embedding vector_cosine_ops) WITH (ef_construction=256);
Create an S3 Bucket
AWS Simple Storage Service (S3) is one of the storage services provided by AWS. S3 commonly stores data, including images, web application content, backups, logs, and more. Each S3 bucket has a globally unique name and is inaccessible to the public by default.
We need a storage to store the data for our RAG. In this lab, we will use an S3 bucket as the data source for the knowledge base.
In this task, we'll create an S3 Bucket and upload our data source file. After the completion of this task, the provisioned infrastructure would be similar to the one shown in the figure below:
Architecture diagram
Create an S3 bucket

Follow the given steps to create an S3 bucket.
Open the AWS Management Console and search "S3" on the AWS Management Console. Click "S3" from the search results to open the S3 dashboard.

Click the "Create bucket" button.

In the general configuration tab, make sure that the "AWS Region" is set to "US East (N. Virginia) us-east-1." If not, switch to the "N.Virgina" region using the drop-down menu next to the user name at the top right of the screen.

Enter a name for the bucket. For this lab, name the bucket as clab-bucket-<RANDOM_TEXT>. Replace <RANDOM_TEXT> with any random text. You can copy the lab user's account number by clicking the username on the top right corner of the AWS Management Console.

In the "Block Public Access settings for this bucket" section, uncheck the "Block all public access" option. Acknowledge the public access warning by checking it.

Leave the rest of the settings as they are. Scroll to the end of the page and click the "Create bucket" button. You will now be redirected to the S3 Buckets page.

We've successfully created an S3 bucket. Let's upload our file to it.
Upload files to S3 Bucket

Follow the steps below to upload files to the bucket:
Search "S3" in the search bar to open the S3 dashboard. Click "General purpose buckets" on the sidebar to list the buckets.

Click the bucket name we've just created. We'll be redirected to the bucket page.

On the "Objects" tab, click the "Upload" button. We'll be redirected to the upload page.

Click the "Add files" button in the "Files and folders" section.

Download the Bedrock and SageMaker file. Upload it to the bucket and click the "Upload" button. Close the success prompt to be redirected to the "Objects" tab.

We've successfully uploaded our content to the bucket. Now, let's create a Knowledge Base with an S3 bucket as a source.

Create a Knowledge Base
Amazon Bedrock Knowledge Bases is a fully managed repository for vector embeddings. It provides more contextual information to foundational models and agents. It helps us implement comprehensive RAG workflows, from ingestion to retrieval and prompt augmentation, without requiring custom integrations with data sources or managing data flows.
In this task, we'll create a knowledge base with an S3 bucket as the source. The knowledge base will fetch the data from the S3 bucket and invoke the Titan Embeddings model to create vector embeddings of the source data. These embeddings will be stored in the Aurora Serverless instance.
The provisioned infrastructure at the end of the task is shown below:
Architecture diagram
Create a Bedrock knowledge base

Follow these steps to create a Bedrock knowledge base:
Click the "Knowledge Bases" under the "Build" from the left navigation menu.

Click the "Create" button and select "Knowledge Base with vector store" from the drop-down menu.

Set "Knowledge base name" as clab-knowledge-base in the "Knowledge base details" section.

Select "Use an existing service role" from the "IAM permissions" section. Select the "AmazonBedrockExecutionRoleForKnowledgeBase" option from the "Choose an existing role or create a new one" drop-down list.

Show the "AmazonBedrockExecutionRoleForKnowledgeBase" policy
Ensure that "Amazon S3" is selected from the "Choose data source type" section. Leave the rest of the settings to default, and click the "Next" button.

On the "Configure data source" page:

Click the "Browse S3" button, select clab-bucket-<RANDOM_TEXT> we created previously, and click the "Choose" button.

Keep the "Chunking strategy" as default and click the "Next" button.

On the "Configure data storage and processing" page:

Click the "Select model" button under the "Embedding model".

Select the "Titan Text Embeddings v2" model in the "Select model" pop-up, and click the "Apply" button.

In the "Vector store" section, select the "Use an existing vector store" option and select "Aurora PostgreSQL Serverless" from the "Vector store type" drop-down list.

In the "Amazon Aurora DB Cluster ARN" field, enter the ARN of the RDS cluster we saved in the previous task.

Enter the VectorDatabase in the "Database name" field.

Enter the bedrock_integration.bedrock_kb in the "Table name" field.

In the "Secret ARN" field, enter the ARN of the secret with the name starting with rds!cluster, we saved in the previous task.

In the "Index field mapping" and "Metadata field mapping" sections, map the columns of the Aurora table:

Enter embedding in the "Vector field name" field.

Enter chunks in the "Text field name" field.

Enter metadata in the "Bedrock-managed metadata field" field.

Enter id in the "Primary key" field.

Click the "Next" button.

Review the configurations and click the "Create Knowledge Base" button.

Sync the data source

We'll be on our knowledge base page. We are one step away from querying our knowledge base. Once the knowledge base's status is "Available," we can sync the data source.
In the "Data source" section, select the knowledge base we have created.

Click the "Sync" button from the "Data source" section.

After the success message, our data from the S3 bucket is converted to vectors, which are stored in the RDS database. Now, we can query the data to search from our knowledge base.
Note: In the "Knowledge base overview" tab, copy the "Knowledge base ID" as needed in the next task.

In the next task, we'll design our LangChain application.

Create a LangChain Application
LangChain is an open-source framework designed to simplify and standardize the development of applications using language models (LMs), such as those from OpenAI, Cohere, and others. It provides tools to help developers build more complex, interactive, and efficient applications that rely on LMs, such as chatbots, question-answering systems, and document retrieval apps.
In this task, we'll create a LangChain application to answer queries about Bedrock and SageMaker's differences. The architecture diagram below shows the infrastructure at the end of this task:
Code overview

We aim to develop a LangChain chatbot to answer queries about the differences between SageMaker and Bedrock. We have already prepared our knowledge base using Bedrock Knowledge Bases. In this application, we'll fetch the embedding and use the Claude LLM to understand the user query and generate responses using the knowledge base.
Copy the model ID for the Anthropic Claude Haiku 3.5 model

To invoke the Anthropic Claude Haiku 3.5 model for text generation, we need the inference profile ID in our code. Follow the steps below to get the ID of the inference profile for Haiku 3.5:
Navigate to the Bedrock dashboard and select "Cross-region inference" from the side bar menu under the "Infer" heading.

Search for US Anthropic Claude Haiku 4.5 in the search field then select Name = US Anthropic Claude Haiku 4.5 option and copy its "Inference profile ID".

In the code below, replace <CLAUDE_INFERENCE_PROFILE_ID> on line 24 with the inference profile ID and save the code.

Now, let's run the application.
Run the application

The code widget given below shows the LangChain chatbot. Before running the code, replace
<KNOWLEDGE_BASE_ID> on line 12 with the ID of the knowledge base we copied in the previous task.

Click the "Run" button to run the application. The application output answers the query "What is SageMaker?".
Code explanation

Let's understand the code line by line:
Lines 1–3: We set the environment variables to limit the number of threads used by libraries that use OpenBLAS or OMP It's often used to optimize performance, especially in multi-threaded systems. We'll be needing it for the langchain_community.chat_models library.

Lines 5–10: We import the necessary langchain libraries to create the generator and retriever and boto3 to fetch the knowledge base.

Line 12: We define the ID of our knowledge base.

Lines 14–21: We define a function to get the Bedrock client using the AWS access keys and secret access keys.

Lines 23–61: We define a function to create the retriever of the LangChain application.

Lines 24–31: We define the model of the LLM generator and set the keyword arguments required by the model in the API call.

How to get the required keywords arguments
Lines 33–38: We define a template format for the input to the AI model. This format will combine the question and context to instruct the model on how to answer.

Lines 41–44: We define a retriever to fetch the context from the knowledge base to answer the query. It uses vector search to retrieve the most relevant documents. The numberOfResults parameter specifies how many results to retrieve.

Lines 46–47: We define the LLM generator, which uses the Bedrock client and model ID of the Anthropic Calude model.

Line 50: We define a conversation buffer memory to retain the memory of previous conversations. This will allow the LangChain chatbot to store the conversation history and remember context across multiple exchanges with the user.

Lines 51–57: We define the retrieval QA which integrated the knowledge base retriever with the LLM generator. We can pass our queries to this object to generate the answer.

Line 58: The function returns the retrieval QA and the buffer memory.

Line 61: We call the function create_retrieval_qa() to get retrieval QA and the buffer memory.

Line 62–65: We pass the query to the retrieval QA to get the answer and print it on the console.

Line 68–71: We save the response context in the buffer memory.

We have successfully created our LangChain chatbot. In the next task, we'll add Streamlit frontend to this

Create a Streamlit Application
Streamlit is an open-source Python framework that enables the rapid creation of interactive web applications, specifically for machine learning, data science, and analytics projects. With Streamlit, we can turn data scripts into interactive applications with minimal effort, making it ideal for showcasing models, data visualizations, and analysis.
We'll use Streamlit to create our application's frontend and ask queries in this task.
Code overview

The code widget below shows the code for our LangChain chatbot with Streamlit frontend. Notice that it contains two files:
bedrock_chat.py: This file contains the code for the LangChain chatbot we created in the previous task. The code in this file is similar to the one we discussed in the previous task.

app.py: This file contains the code for the Streamlit frontend application.

Test the application

Now, let's run the code to execute our Streamlit application. Before clicking the "Run" button, replace the <KNOWLEDGE-BASE-ID> on line 13 in bedrock_chat.py with the ID of the knowledge base. Also, we have added us.anthropic.claude-haiku-4-5-20251001-v1:0 inference profile ID of the Haiku 4.5 model on line 31.

Clean Up
Let's end this lab by cleaning up all the resources we've created.
Delete the Bedrock knowledge base

Open the Bedrock dashboard by searching for "Bedrock" in the search bar and selecting "Knowledge base" from the sidebar menu.

Select the knowledge base and click the "Delete" button.

⚠️ Warning: Do not delete the data source before deleting the knowledge base. By default, the data retention policy for Bedrock is set to "Delete," which throws an error while deleting the knowledge base.

Delete the RDS database

Follow the steps below to delete the database:
Navigate to the RDS dashboard.

Select the database instance and click "Actions." Here, select "Delete," enter "delete me" in the prompt, and then click "Delete."

After the instance is deleted, click the database and click "Delete." Disable "Create final snapshot" and acknowledge that automated backups, including system snapshots and point-in-time recovery, will no longer be available upon instance deletion. Enter "delete me" in the text box and delete the DB cluster.

Note: It can take up to 10 minutes to delete the database.

Delete the S3 bucket

Before we delete our S3 bucket, we must empty it. Follow the given steps to empty our S3 bucket:
Head over to the "Amazon S3 > Buckets" page and search for your S3 bucket.

Click the name of the S3 bucket clab-bucket-<RANDOM_TEXT>.

Select the S3 bucket we had created and click "Empty." Enter "permanently delete" in the text field and click "Empty."

After the bucket is emptied, we'll see a success message. Click the "Exit" button.

Now that we've emptied the S3 bucket, we can delete the S3 bucket itself. Follow the given steps to delete the S3 bucket:
Select the bucket from the bucket list.

Click the "Delete" button.

Enter the bucket name in the text box to confirm deletion and click the "Delete bucket" button.