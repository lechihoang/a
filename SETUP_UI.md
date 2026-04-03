# Setup bằng UI (Azure Portal) + CLI — từng bước

Mục tiêu: dựng lại môi trường demo, dùng UI/CLI tùy bước cho tiện. CI/CD tự động deploy từ GitHub Actions.

## 1) Tạo Resource Group
1. Vào **Azure Portal** → **Resource groups** → **Create**.
2. Name: `uk-property-rg`
3. Region: `Southeast Asia`
4. Bấm **Review + create** → **Create**.

---

## 2) Tạo Storage Account
1. Vào **Storage accounts** → **Create**.
2. Resource group: `uk-property-rg`
3. Storage account name: `ukpropaistg` (nếu trùng, đổi tên khác)
4. Region: `Southeast Asia`
5. Performance: `Standard`
6. Redundancy: `LRS`
7. Bấm **Review + create** → **Create**.

### 2.1 Tạo Blob container `rawdata`
1. Vào storage account `ukpropaistg` → **Data storage** → **Containers**.
2. Bấm **+ Container**.
3. Name: `rawdata` → **Create**.

### 2.2 Tạo File Share `processed`
1. Vào storage account `ukpropaistg` → **Data storage** → **File shares**.
2. Bấm **+ File share**.
3. Name: `processed` → **Create**.

### 2.3 Upload file raw CSV (CLI)
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

---

## 3) Tạo Container Apps Environment
```bash
az containerapp env create \
  --name project-env \
  --resource-group uk-property-rg \
  --location southeastasia
```

---

## 4) Tạo Azure Container Registry (ACR)
1. Vào **Container registries** → **Create**.
2. Resource group: `uk-property-rg`
3. Registry name: `ukpropacr`
4. SKU: `Basic`
5. Region: `Southeast Asia`
6. **Review + create**.

> Không bắt buộc bật Admin user nếu dùng Managed Identity + `AcrPull`.

---

## 4.5) Push code lên GitHub (trigger CI/CD build image)
1. Commit & push code lên repository GitHub (branch `main`).
2. GitHub Actions sẽ tự động build Docker image và push lên ACR.
3. Chờ pipeline chạy xong (1–3 phút).

---

## 5) Tạo Container App bằng CLI
## 5) Tạo Container App bằng CLI
```bash
az acr update -n ukpropacr --admin-enabled true

ACR_USER=$(az acr credential show --name ukpropacr --query username -o tsv)
ACR_PASS=$(az acr credential show --name ukpropacr --query 'passwords[0].value' -o tsv)

az containerapp create \
  --name uk-property-app \
  --resource-group uk-property-rg \
  --environment project-env \
  --image ukpropacr.azurecr.io/uk-property-app:latest \
  --registry-server ukpropacr.azurecr.io \
  --registry-username "$ACR_USER" \
  --registry-password "$ACR_PASS" \
  --ingress external \
  --target-port 8501 \
  --cpu 4 --memory 8Gi
```

---

## 6) Bật Managed Identity cho app
1. Vào `uk-property-app` → **Identity**.
2. Tab **System assigned** → **On** → **Save**.

---

## 7) Gán quyền cho Managed Identity (Storage + ACR)
1. Vào storage account `ukpropaistg` → **Access control (IAM)** → **Add role assignment**.
2. Thêm role:
   - `Storage Blob Data Reader`
   - assignee: managed identity của `uk-property-app`
3. Thêm tiếp role:
   - `Storage File Data Privileged Contributor`
   - assignee: managed identity của `uk-property-app`

4. Vào ACR `ukpropacr` → **Access control (IAM)** → **Add role assignment**.
5. Thêm role:
   - `AcrPull`
   - assignee: managed identity của `uk-property-app`

---

## 8) Đổi auth pull image sang Managed Identity
```bash
az containerapp registry set \
  --name uk-property-app \
  --resource-group uk-property-rg \
  --server ukpropacr.azurecr.io \
  --identity system
```

---

## 9) Mount Azure File Share vào Container App
### 10.1 Khai báo storage ở Environment
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

az containerapp env storage list --name project-env --resource-group uk-property-rg -o table
```

### 10.2 Gắn volume vào app
```bash
az containerapp update \
  --name uk-property-app \
  --resource-group uk-property-rg \
  --volume "processedfiles" \
  --mount-path "/mnt/processed"
```

---

## 10) Bật autoscale (KEDA HTTP)
1. Vào `uk-property-app` → **Scale**.
2. Min replicas: `1`
3. Max replicas: `5`
4. Thêm/điều chỉnh HTTP scale rule:
   - Concurrent requests: `20`
5. Save.

---

## 11) Lấy URL và kiểm tra
1. Vào `uk-property-app` → **Overview**.
2. Mở Application URL.
3. Nếu lỗi quyền, đợi 2–5 phút cho IAM propagate rồi **restart revision**.

---

## 12) Khi cần xem log trên UI
1. Vào `uk-property-app` → **Monitoring** → **Logs / Log stream**.
2. Theo dõi lỗi runtime và startup.

---

## 13) CI/CD: Deploy tự động từ GitHub Actions

Sau khi push code lên branch `main`, GitHub Actions sẽ tự động:
1. Build Docker image → push lên ACR
2. Update Container App (image mới)
3. Mount volume + restart revision

Xem chi tiết: `.github/workflows/deploy.yml`

---

## Checklist nhanh trước khi demo
- [ ] App chạy ổn định với `4 CPU / 8Gi`
- [ ] Managed Identity đã bật
- [ ] Có đủ 3 role: Blob Reader, File Privileged Contributor, AcrPull
- [ ] Registry pull dùng `--identity system`
- [ ] Volume `processedfiles` mount tại `/mnt/processed`
- [ ] Ingress external + port `8501`
- [ ] Scale: min 1, max 5, concurrency 20



az ad sp create-for-rbac --skip-assignment