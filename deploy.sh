#!/bin/bash
# deploy.sh - Deployment script for Azure Functions

set -e

# Configuration
RESOURCE_GROUP="rg-recommender-app"
LOCATION="francecentral"
STORAGE_ACCOUNT="strecommenderdata"
FUNCTION_APP="func-recommender-api"
CONTAINER_NAME="data"
PYTHON_VERSION="3.11"

echo "========================================="
echo "Azure Recommender App Deployment"
echo "========================================="

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed"
    echo "Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Login to Azure (if not already logged in)
echo "Checking Azure login status..."
az account show &> /dev/null || az login

# Create resource group
echo "Creating resource group: $RESOURCE_GROUP in $LOCATION..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
echo "Creating storage account: $STORAGE_ACCOUNT..."
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2

# Get storage account connection string
echo "Retrieving storage account connection string..."
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query connectionString \
    --output tsv)

# Create blob container
echo "Creating blob container: $CONTAINER_NAME..."
az storage container create \
    --name $CONTAINER_NAME \
    --connection-string "$STORAGE_CONNECTION_STRING"

# Upload data files to blob storage
echo "Uploading data files to blob storage..."
if [ -d "../dataset" ]; then
    echo "  - Uploading clicks.csv..."
    az storage blob upload \
        --container-name $CONTAINER_NAME \
        --file ../dataset/clicks.csv \
        --name clicks.csv \
        --connection-string "$STORAGE_CONNECTION_STRING" \
        --overwrite

    echo "  - Uploading articles_metadata.csv..."
    az storage blob upload \
        --container-name $CONTAINER_NAME \
        --file ../dataset/articles_metadata.csv \
        --name articles_metadata.csv \
        --connection-string "$STORAGE_CONNECTION_STRING" \
        --overwrite

    echo "  - Uploading articles_embeddings_reduced.pickle..."
    az storage blob upload \
        --container-name $CONTAINER_NAME \
        --file ../dataset/articles_embeddings_reduced.pickle \
        --name articles_embeddings_reduced.pickle \
        --connection-string "$STORAGE_CONNECTION_STRING" \
        --overwrite
else
    echo "Warning: ../dataset directory not found. Please upload data files manually."
fi

# Create Function App
echo "Creating Function App: $FUNCTION_APP..."
az functionapp create \
    --resource-group $RESOURCE_GROUP \
    --name $FUNCTION_APP \
    --storage-account $STORAGE_ACCOUNT \
    --consumption-plan-location $LOCATION \
    --runtime python \
    --runtime-version $PYTHON_VERSION \
    --functions-version 4 \
    --os-type Linux

# Configure app settings
echo "Configuring Function App settings..."
az functionapp config appsettings set \
    --name $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP \
    --settings \
        "STORAGE_CONTAINER=$CONTAINER_NAME" \
        "PYTHON_ISOLATE_WORKER_DEPENDENCIES=1"

# Deploy function app
echo "Deploying function app code..."
func azure functionapp publish $FUNCTION_APP --python

echo "========================================="
echo "Deployment completed successfully!"
echo "========================================="
echo ""
echo "Function App URL: https://$FUNCTION_APP.azurewebsites.net"
echo ""
echo "Available endpoints:"
echo "  - Health check: https://$FUNCTION_APP.azurewebsites.net/api/health"
echo "  - Users list:   https://$FUNCTION_APP.azurewebsites.net/api/users"
echo "  - Recommend:    https://$FUNCTION_APP.azurewebsites.net/api/recommend?user_id=123"
echo ""
echo "To view logs:"
echo "  az functionapp logs tail --name $FUNCTION_APP --resource-group $RESOURCE_GROUP"
echo ""
