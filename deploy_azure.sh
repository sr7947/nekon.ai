#!/bin/bash
set -euo pipefail

# =============================================================================
# nekon.ai — Azure Infrastructure Deployment Script
# Provisions: Azure Resource Group, Azure AI Foundry Hub + Project, GPT Model,
# Log Analytics Workspace, and Application Insights Instance
# =============================================================================

# Prevent Git Bash on Windows from converting /subscriptions/... into C:\Program Files\Git\...
export MSYS_NO_PATHCONV=1

# Auto-install CLI extensions without interactive prompts
az config set extension.use_dynamic_install=yes_without_prompt --only-show-errors >/dev/null 2>&1 || true
az extension add --name application-insights --only-show-errors >/dev/null 2>&1 || true

echo "================================================================="
echo "  nekon.ai — Azure AI Foundry Infrastructure Deployment"
echo "================================================================="

# --- Configuration & Defaults ------------------------------------------------
SUFFIX="${SUFFIX:-$(openssl rand -hex 4 2>/dev/null || echo "1790")}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-nekon-ai-$SUFFIX}"
LOCATION="${LOCATION:-eastus2}"
FOUNDRY_RESOURCE_NAME="${FOUNDRY_RESOURCE_NAME:-nekon-foundry-$SUFFIX}"
PROJECT_NAME="${PROJECT_NAME:-nekon-ai-project}"
MODEL_DEPLOYMENT_NAME="${MODEL_DEPLOYMENT_NAME:-gpt-4o}"
MODEL_NAME="${MODEL_NAME:-gpt-4o}"
MODEL_VERSION="${MODEL_VERSION:-2024-08-06}"
LOG_ANALYTICS_NAME="${LOG_ANALYTICS_NAME:-nekon-logs-$SUFFIX}"
APP_INSIGHTS_NAME="${APP_INSIGHTS_NAME:-nekon-insights-$SUFFIX}"

# --- Step 1: Azure Login Check -----------------------------------------------
echo ""
echo "[1/6] Verifying Azure CLI authentication..."
if ! az account show >/dev/null 2>&1; then
    echo "❌ Azure CLI is not logged in. Please run 'az login' first."
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo "✅ Authenticated as Subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

# --- Step 2: Create Resource Group -------------------------------------------
echo ""
echo "[2/6] Creating Resource Group '$RESOURCE_GROUP' in '$LOCATION'..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output table

# --- Step 3: Create Log Analytics & Application Insights ---------------------
echo ""
echo "[3/6] Provisioning Log Analytics Workspace & Application Insights..."
az monitor log-analytics workspace create \
    --resource-group "$RESOURCE_GROUP" \
    --workspace-name "$LOG_ANALYTICS_NAME" \
    --location "$LOCATION" \
    --output table || true

LOG_WORKSPACE_ID=$(az monitor log-analytics workspace show \
    --resource-group "$RESOURCE_GROUP" \
    --workspace-name "$LOG_ANALYTICS_NAME" \
    --query id -o tsv)

az monitor app-insights component create \
    --app "$APP_INSIGHTS_NAME" \
    --location "$LOCATION" \
    --resource-group "$RESOURCE_GROUP" \
    --workspace "$LOG_WORKSPACE_ID" \
    --output table || true

APPINSIGHTS_CONN_STRING=$(az monitor app-insights component show \
    --app "$APP_INSIGHTS_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query connectionString -o tsv)

echo "✅ Application Insights Connection String retrieved."

# --- Step 4: Create Azure AI Foundry Resource --------------------------------
echo ""
echo "[4/6] Creating Azure AI Foundry Resource '$FOUNDRY_RESOURCE_NAME'..."
az cognitiveservices account create \
    --name "$FOUNDRY_RESOURCE_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --kind "AIServices" \
    --sku "S0" \
    --custom-domain "$FOUNDRY_RESOURCE_NAME" \
    --output table || true

# --- Step 5: Create Azure AI Foundry Project ----------------------------------
echo ""
echo "[5/6] Creating Azure AI Foundry Project '$PROJECT_NAME'..."
az cognitiveservices account projects create \
    --name "$FOUNDRY_RESOURCE_NAME" \
    --project-name "$PROJECT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output table || true

# --- Step 6: Deploy GPT Model -------------------------------------------------
echo ""
echo "[6/6] Deploying GPT Model '$MODEL_DEPLOYMENT_NAME' ($MODEL_NAME version $MODEL_VERSION)..."
az cognitiveservices account deployment create \
    --name "$FOUNDRY_RESOURCE_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --deployment-name "$MODEL_DEPLOYMENT_NAME" \
    --model-name "$MODEL_NAME" \
    --model-version "$MODEL_VERSION" \
    --model-format OpenAI \
    --sku-name "Standard" \
    --sku-capacity 10 \
    --output table || true

# --- Construct Connection String --------------------------------------------
PROJECT_CONN_STR="$LOCATION.api.azureml.ms;$SUBSCRIPTION_ID;$RESOURCE_GROUP;$PROJECT_NAME"

echo ""
echo "================================================================="
echo "  🎉 DEPLOYMENT COMPLETE FOR NEKON.AI"
echo "================================================================="
echo "  Resource Group    : $RESOURCE_GROUP"
echo "  Location          : $LOCATION"
echo "  Foundry Resource  : $FOUNDRY_RESOURCE_NAME"
echo "  Foundry Project   : $PROJECT_NAME"
echo "  Model Deployment  : $MODEL_DEPLOYMENT_NAME"
echo ""
echo "  PROJECT_CONNECTION_STRING=$PROJECT_CONN_STR"
echo "  APPLICATIONINSIGHTS_CONNECTION_STRING=$APPINSIGHTS_CONN_STRING"
echo "================================================================="
echo ""
echo "To update your local .env file automatically:"
echo "cat <<EOF > .env"
echo "PROJECT_CONNECTION_STRING=$PROJECT_CONN_STR"
echo "MODEL_DEPLOYMENT_NAME=$MODEL_DEPLOYMENT_NAME"
echo "APPLICATIONINSIGHTS_CONNECTION_STRING=$APPINSIGHTS_CONN_STRING"
echo "AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING=true"
echo "WORKFLOW_AGENT_NAME=nekon-intelligence-hub-workflow"
echo "EOF"
