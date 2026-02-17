# Microsoft Sentinel Dynamic Ingestion Accelerator

An automated solution for ingesting dynamic JSON data into Microsoft Sentinel using the Azure Monitor Ingestion API with Data Collection Rules (DCR). This accelerator simplifies the process of sending custom log data to Sentinel workspaces.

> **Note**: This is a testing and development accelerator. For production use, implement proper security practices such as Azure Key Vault for secrets management and managed identities.

## 📋 What's Included

- **`deploy-arm-template.json`** - ARM template that deploys:
  - Custom log table (`TestData_CL`) with dynamic RawData column
  - Data Collection Endpoint (DCE)
  - Data Collection Rule (DCR)
- **`test_sentinel_ingestion.py`** - Python script for testing data ingestion to Sentinel
- **`rawData.png`** - Visual reference of the dynamic data structure

## 🎯 Prerequisites

- **Existing Log Analytics/Sentinel Workspace** in Azure
- **Azure PowerShell** or **Azure CLI** installed
- **Python 3.7+** with pip
- **Azure Permissions**:
  - Create App Registrations (Microsoft Entra ID)
  - Deploy ARM templates to resource groups
  - Assign RBAC roles on Data Collection Rules

## 🚀 Quick Start

### Step 1: Clone Repository

```bash
git clone https://github.com/robertmoriarty12/Sentinel-Dynamic-Ingestion-API-Accelerator.git
cd Sentinel-Dynamic-Ingestion-API-Accelerator
```

### Step 2: Create App Registration

#### Using PowerShell:
```powershell
# Connect to Azure
Connect-AzAccount

# Create App Registration
$appName = "SentinelTestIngestion"
$app = New-AzADApplication -DisplayName $appName
$sp = New-AzADServicePrincipal -ApplicationId $app.AppId
$secret = New-AzADAppCredential -ApplicationId $app.AppId -EndDate (Get-Date).AddYears(1)

# Save these values
Write-Host "Client ID: $($app.AppId)"
Write-Host "Tenant ID: $((Get-AzContext).Tenant.Id)"
Write-Host "Client Secret: $($secret.SecretText)"
```

#### Using Azure CLI:
```bash
# Create App Registration
APP_NAME="SentinelTestIngestion"
APP_ID=$(az ad app create --display-name $APP_NAME --query appId -o tsv)
az ad sp create --id $APP_ID
SECRET=$(az ad app credential reset --id $APP_ID --append --query password -o tsv)

# Display values
echo "Client ID: $APP_ID"
echo "Tenant ID: $(az account show --query tenantId -o tsv)"
echo "Client Secret: $SECRET"
```

⚠️ **Save these credentials immediately - you cannot retrieve the secret later!**

### Step 3: Deploy ARM Template

#### Using PowerShell:

```powershell
# Deploy the ARM template
New-AzResourceGroupDeployment `
  -ResourceGroupName "your-resource-group-name" `
  -TemplateFile .\deploy-arm-template.json `
  -workspaceName "your-sentinel-workspace-name"
```

#### Using Azure CLI:
```bash
az deployment group create \
  --resource-group your-resource-group-name \
  --template-file deploy-arm-template.json \
  --parameters workspaceName=your-sentinel-workspace-name
```

⏱️ **Deployment takes 2-5 minutes**

### Step 4: Capture Deployment Outputs

After deployment completes, save these output values:

#### PowerShell:
```powershell
$deployment = Get-AzResourceGroupDeployment `
  -ResourceGroupName "your-resource-group-name" `
  -Name "deploy-arm-template"

# Display outputs
$deployment.Outputs.dataCollectionEndpointUrl.Value
$deployment.Outputs.dataCollectionRuleImmutableId.Value
$deployment.Outputs.streamName.Value
```

#### Azure CLI:
```bash
az deployment group show \
  --resource-group your-resource-group-name \
  --name deploy-arm-template \
  --query "properties.outputs"
```

**Save these values:**
- `dataCollectionEndpointUrl` = Your **DCE_ENDPOINT**
- `dataCollectionRuleImmutableId` = Your **DCR_ID** (starts with `dcr-`)
- `streamName` = Your **STREAM_NAME** (typically `Custom-TestData_CL`)

### Step 5: Assign Permissions

Grant the App Registration the **Monitoring Metrics Publisher** role on the Data Collection Rule.

#### PowerShell:
```powershell
$dcrId = "/subscriptions/YOUR_SUB_ID/resourceGroups/YOUR_RG/providers/Microsoft.Insights/dataCollectionRules/TestDataDCR"
$spId = "YOUR_SERVICE_PRINCIPAL_OBJECT_ID"  # From Step 2

# Wait for service principal to propagate
Start-Sleep -Seconds 15

# Assign role
New-AzRoleAssignment `
  -ObjectId $spId `
  -RoleDefinitionName "Monitoring Metrics Publisher" `
  -Scope $dcrId
```

#### Azure CLI:
```bash
DCR_ID="/subscriptions/YOUR_SUB_ID/resourceGroups/YOUR_RG/providers/Microsoft.Insights/dataCollectionRules/TestDataDCR"
SP_ID="YOUR_SERVICE_PRINCIPAL_OBJECT_ID"

az role assignment create \
  --assignee $SP_ID \
  --role "Monitoring Metrics Publisher" \
  --scope $DCR_ID
```

⏱️ **Wait 2-3 minutes** for role assignment to propagate

### Step 6: Install Python Dependencies

```bash
pip install azure-identity azure-monitor-ingestion
```

### Step 7: Configure Python Script

Edit `test_sentinel_ingestion.py` and update the configuration section:

```python
# Azure AD App Registration credentials
TENANT_ID = "your-tenant-id"          # From Step 2
CLIENT_ID = "your-client-id"          # From Step 2
CLIENT_SECRET = "your-client-secret"  # From Step 2

# Data Collection Endpoint and Rule
DCE_ENDPOINT = "https://your-dce-endpoint.ingest.monitor.azure.com"  # From Step 4
DCR_ID = "dcr-xxxxxxxxxxxxx"          # From Step 4
STREAM_NAME = "Custom-TestData_CL"    # From Step 4
```

### Step 8: Run the Test Script

```bash
python test_sentinel_ingestion.py
```

**Expected output:**
```
======================================================================
Microsoft Sentinel Test Data Ingestion Script
Using Azure Monitor Ingestion API (DCE/DCR)
======================================================================

...

======================================================================
✓ SUCCESS! Data has been ingested.
  Records sent: 2
  Response: HTTP 204 No Content (success)
  Timestamp: 2026-02-17 19:50:06 UTC

To query your data in Sentinel, use this KQL query:
  TestData_CL | take 10

Note: It may take 5-10 minutes for data to appear in Sentinel
======================================================================
```

### Step 9: Query Data in Sentinel

⏱️ **Wait 5-20 minutes** for data indexing

1. Navigate to **Microsoft Sentinel** → Your workspace → **Logs**
2. Run this KQL query:

```kusto
TestData_CL
| take 10
```

View dynamic data:
```kusto
TestData_CL
| project TimeGenerated, RawData
| extend SchemaType = RawData.SchemaType
| take 10
```

## 📊 Data Schema

The custom table includes:

| Field | Type | Description |
|-------|------|-------------|
| TimeGenerated | datetime | Ingestion timestamp |
| RawData | dynamic | JSON object containing flexible schema data |
| _ResourceId | string | Azure resource identifier |

### Sample RawData Structure

```json
{
  "SchemaType": "UserLogin",
  "UserId": "user123",
  "Action": "Login",
  "Details": {
    "IP": "192.168.1.1",
    "Success": true
  }
}
```

## 🔧 Troubleshooting

### Authentication Error: AADSTS700016

**Problem**: App not found in directory

**Solution**: Ensure you created the App Registration in the **same tenant** as your Azure subscription. Run:
```powershell
Get-AzContext | Select-Object Account, Tenant
```

### Permission Error: 403 Forbidden

**Problem**: Insufficient permissions to send data

**Solution**:
1. Verify role assignment: Navigate to DCR → **Access control (IAM)** → **Role assignments**
2. Look for your App Registration under **Monitoring Metrics Publisher**
3. Wait 2-5 minutes after role assignment for propagation

### Data Not Appearing in Sentinel

**Problem**: Script succeeds but no data visible

**Solution**:
- Wait longer (up to 20 minutes for first ingestion)
- Verify table exists: Navigate to **Sentinel** → **Settings** → **Workspace settings** → **Tables**
- Check for `TestData_CL` in the tables list
- Run: `TestData_CL | count` to verify records exist

### Module Not Found Error

**Problem**: `ModuleNotFoundError: No module named 'azure.monitor'`

**Solution**:
```bash
pip install --upgrade azure-identity azure-monitor-ingestion
```

## 🎨 Customization

### Modify Data Structure

To send different data:

1. Edit the `sample_data` list in `test_sentinel_ingestion.py`
2. Update the JSON structure in `RawData`
3. No ARM template changes needed (dynamic column)

**Example:**
```python
sample_data = [
    {
        "TimeGenerated": datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "RawData": {
            "EventType": "SecurityAlert",
            "Severity": "High",
            "Description": "Suspicious activity detected",
            "SourceIP": "10.0.0.1"
        }
    }
]
```

### Change Table Schema

To add fixed columns (beyond RawData):

1. Edit `deploy-arm-template.json` → `columns` array
2. Redeploy ARM template
3. Update Python script data structure

## 🧹 Cleanup

### Delete Data Collection Resources

```powershell
# Delete Data Collection Rule
Remove-AzDataCollectionRule -ResourceGroupName "your-rg" -Name "TestDataDCR"

# Delete Data Collection Endpoint
Remove-AzDataCollectionEndpoint -ResourceGroupName "your-rg" -Name "testdata-dce"
```

### Delete App Registration

```powershell
Remove-AzADApplication -ApplicationId "your-client-id"
```

⚠️ **Note**: Custom log tables (`TestData_CL`) cannot be deleted but won't incur costs unless data is actively ingested.

## 📚 Resources

- [Azure Monitor Ingestion API](https://learn.microsoft.com/azure/azure-monitor/logs/logs-ingestion-api-overview)
- [Data Collection Rules](https://learn.microsoft.com/azure/azure-monitor/essentials/data-collection-rule-overview)
- [Microsoft Sentinel Custom Logs](https://learn.microsoft.com/azure/sentinel/connect-custom-logs)
- [Azure Monitor Python SDK](https://learn.microsoft.com/python/api/overview/azure/monitor-ingestion-readme)

## ⚠️ Security Best Practices

For production deployments:

- ✅ Store secrets in **Azure Key Vault**
- ✅ Use **Managed Identities** instead of client secrets
- ✅ Implement **certificate-based authentication**
- ✅ Enable **diagnostic logging** on DCR
- ✅ Rotate secrets regularly
- ✅ Use **least privilege** RBAC assignments
- ✅ Implement **network restrictions** on DCE

## 💡 Support

For issues:
1. Check the **Troubleshooting** section above
2. Review deployment outputs and error messages
3. Verify all configuration values match
4. Check Azure Monitor logs for DCR/DCE diagnostics

## 📝 License

This project is provided as-is for testing and acceleration purposes.

---

**Last Updated**: February 2026
