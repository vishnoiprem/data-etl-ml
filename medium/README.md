# =============================================================================
# requirements.txt
# =============================================================================
langchain==0.2.0
langchain-openai==0.1.7
langchain-community==0.2.0
langserve[all]==0.2.0
fastapi==0.111.0
uvicorn[standard]==0.30.0
pydantic==2.7.1
httpx==0.27.0
python-dotenv==1.0.1


# =============================================================================
# .env  (never commit this to git)
# =============================================================================
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
LANGCHAIN_API_KEY=your-langsmith-key        # optional — for tracing
LANGCHAIN_TRACING_V2=true                   # optional — enables LangSmith


# =============================================================================
# How to run locally
# =============================================================================
# 1. Install:
#    pip install -r requirements.txt
#
# 2. Set env vars:
#    cp .env.example .env
#    (fill in your Azure OpenAI keys)
#
# 3. Start server:
#    uvicorn server_api:app --host 0.0.0.0 --port 8000 --reload
#
# 4. Test in browser:
#    http://localhost:8000/docs              ← Swagger UI
#    http://localhost:8000/llm-chain/playground   ← LangServe playground
#    http://localhost:8000/health            ← health check
#
# 5. Test with client:
#    python client.py


# =============================================================================
# Deploy on Azure Container Apps (production)
# =============================================================================
# Dockerfile:

# FROM python:3.11-slim
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install -r requirements.txt
# COPY . .
# EXPOSE 8000
# CMD ["uvicorn", "server_api:app", "--host", "0.0.0.0", "--port", "8000"]

# Build + push:
# docker build -t makro-llm-gateway .
# docker tag makro-llm-gateway <your-acr>.azurecr.io/makro-llm-gateway:v1
# docker push <your-acr>.azurecr.io/makro-llm-gateway:v1
# az containerapp create \
#   --name makro-llm-gateway \
#   --resource-group makro-rg \
#   --image <your-acr>.azurecr.io/makro-llm-gateway:v1 \
#   --target-port 8000 \
#   --ingress external
