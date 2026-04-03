# DEMO (từng lệnh CLI)

## 0) Kích hoạt môi trường
```bash
source /Users/abc/Documents/IS/venv/bin/activate
cd /Users/abc/Documents/IS
```

## 1) Login Azure
```bash
az login
az account set --subscription "Azure subscription 1"
```

## 2) Tạo Resource Group
```bash
az group create --name uk-property-rg --location southeastasia
```

## 3) Register providers
```bash
az provider register -n Microsoft.ContainerRegistry --wait
az provider register -n Microsoft.App --wait
az provider register -n Microsoft.OperationalInsights --wait
```

## 4) Tạo Storage
```bash
az storage account create --name ukpropaistg --resource-group uk-property-rg --sku Standard_LRS
az storage container create --name rawdata --account-name ukpropaistg
az storage share create --name processed --account-name ukpropaistg
```

## 5) Tạo ACR
```bash
az acr create --name ukpropacr --resource-group uk-property-rg --sku Basic
az acr update --name ukpropacr --admin-enabled true
az acr login --name ukpropacr
```

## 6) Tạo Container Apps Environment
```bash
az containerapp env create \
  --name project-env \
  --resource-group uk-property-rg \
  --location southeastasia
```

## 7) Upload raw CSV lên Blob
```bash
start=$(date +%s)
az storage blob upload \
  --account-name ukpropaistg \
  --container-name rawdata \
  --name uk_property_raw.csv \
  --file data/202304.csv
end=$(date +%s)
echo "Upload took $((end - start))s"
```

## 8) Deploy Container App (lần đầu)
```bash
az containerapp create \
  --name uk-property-app \
  --resource-group uk-property-rg \
  --environment project-env \
  --image ukpropacr.azurecr.io/uk-property-app:latest \
  --registry-server ukpropacr.azurecr.io \
  --target-port 8501 \
  --ingress external \
  --cpu 4 --memory 8Gi
```

## 9) Bật Managed Identity
```bash
ACCOUNT_ID=$(az account show --query id -o tsv)
az containerapp identity assign --name uk-property-app --resource-group uk-property-rg --system-assigned
PRINCIPAL_ID=$(az containerapp show --name uk-property-app --resource-group uk-property-rg --query "identity.principalId" -o tsv)
```

## 10) Gán quyền Storage + ACR
```bash
az role assignment create --assignee "$PRINCIPAL_ID" --role "Storage Blob Data Reader" --scope "/subscriptions/$ACCOUNT_ID/resourceGroups/uk-property-rg/providers/Microsoft.Storage/storageAccounts/ukpropaistg"
az role assignment create --assignee "$PRINCIPAL_ID" --role "Storage File Data Privileged Contributor" --scope "/subscriptions/$ACCOUNT_ID/resourceGroups/uk-property-rg/providers/Microsoft.Storage/storageAccounts/ukpropaistg"
az role assignment create --assignee "$PRINCIPAL_ID" --role "AcrPull" --scope "/subscriptions/$ACCOUNT_ID/resourceGroups/uk-property-rg/providers/Microsoft.ContainerRegistry/registries/ukpropacr"
```

## 11) Đổi auth pull image sang Managed Identity
```bash
az containerapp registry set \
  --name uk-property-app \
  --resource-group uk-property-rg \
  --server ukpropacr.azurecr.io \
  --identity system
```

## 12) Mount File Share

### 13.1 Khai báo storage ở Environment
```bash
STG_KEY=$(az storage account keys list --account-name ukpropaistg --resource-group uk-property-rg --query [0].value -o tsv)

az containerapp env storage set \
    --resource-group uk-property-rg \
    --name project-env \
    --storage-name processedfiles \
    --access-mode ReadOnly \
    --account-name ukpropaistg \
    --azure-file-account-key "$STG_KEY" \
    --azure-file-share-name processed
```

### 13.2 Gắn volume vào app
```bash
az containerapp update \
  --name uk-property-app \
  --resource-group uk-property-rg \
  --volume "processedfiles" \
  --mount-path "/mnt/processed"
```

## 13) Cấu hình KEDA autoscale (HTTP)
```bash
az containerapp update --name uk-property-app --resource-group uk-property-rg --min-replicas 1 --max-replicas 5 --scale-rule-name http-rule --scale-rule-http-concurrency 20
```

## 14) Chờ role có hiệu lực + restart revision
```bash
sleep 120
REV=$(az containerapp revision list --name uk-property-app --resource-group uk-property-rg --query "[?properties.active==\`true\`].name | [0]" -o tsv)
az containerapp revision restart --name uk-property-app --resource-group uk-property-rg --revision "$REV"
```

## 15) Lấy URL app
```bash
az containerapp show --name uk-property-app --resource-group uk-property-rg --query "properties.configuration.ingress.fqdn" -o tsv
```

## 16) Xem logs (ETL + Streamlit)
```bash
az containerapp logs show --name uk-property-app --resource-group uk-property-rg --follow
```

## 17) Cleanup
```bash
az group delete --name uk-property-rg --yes --no-wait
```

