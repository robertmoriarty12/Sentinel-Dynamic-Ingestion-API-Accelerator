# Dynamic Ingestion Accelerator for Microsoft Sentinel

A streamlined solution for ingesting dynamic JSON content into Microsoft Sentinel using the Azure Monitor Ingestion API. This accelerator demonstrates how to handle varying data schemas within a single `dynamic` column, allowing for flexible log ingestion without rigid schema constraints.

NOTE: This is just a sample for testing and acceleration. Don't use this directly for production environments without proper security hardening (e.g., Azure Key Vault).

## 📋 Overview

This solution includes:
- **ARM Template** (`deploy-arm-template.json`) - Creates a custom log table with a `dynamic` column (`RawData`), Data Collection Endpoint (DCE), and Data Collection Rule (DCR).
- **Python Script** (`test_sentinel_ingestion.py`) - Sends diverse JSON records (e.g., UserLogin, FileAccess) to Sentinel.
- **Dynamic Schema Strategy** - Instead of defining every column, data is packed into a `RawData` dynamic field.

## 🎯 Prerequisites

Before you begin, ensure you have:

1. **Microsoft Sentinel Instance** - A Sentinel workspace must already be deployed in Azure
2. **Azure CLI or PowerShell** - For deploying ARM templates
3. **Python 3.7+** - For running the ingestion script
4. **Azure Permissions** - Ability to:
   - Create App Registrations in Azure AD
   - Deploy resources to Azure (DCE, DCR, custom tables)
   - Assign RBAC roles on Data Collection Rules

## 🚀 Deployment Steps

### Step 1: Clone the Repository

```bash
git clone https://github.com/Azure/Azure-Sentinel.git
cd Azure-Sentinel/Solutions/cveBuster\ Vulnerability\ Scanning/Server/push_client_web/test
```

### Step 2: Create Azure AD App Registration

1. Navigate to **Azure Portal** → **Azure Active Directory** → **App registrations**
2. Click **+ New registration**
3. Enter a name (e.g., `SentinelTestIngestion`)
4. Leave defaults and click **Register**
5. **Copy the following values** (you'll need them later):
   - **Application (client) ID**
   - **Directory (tenant) ID**
6. Navigate to **Certificates & secrets** → **+ New client secret**
7. Add a description and select expiration period
8. Click **Add** and **immediately copy the secret value** (you won't see it again!)

### Step 3: Deploy the ARM Template

The ARM template creates the necessary Azure resources for data ingestion.

#### Option A: Using Azure CLI

```bash
az deployment group create \
  --resource-group <your-resource-group-name> \
  --template-file deploy-arm-template.json \
  --parameters workspaceName=<your-sentinel-workspace-name>
```

#### Option B: Using PowerShell

```powershell
New-AzResourceGroupDeployment `
  -ResourceGroupName <your-resource-group-name> `
  -TemplateFile .\deploy-arm-template.json `
  -workspaceName <your-sentinel-workspace-name>
```

#### Option C: Using Azure Portal

1. Navigate to **Azure Portal** → **Resource groups** → Select your resource group
2. Click **Create** → Search for "Template deployment (deploy using custom template)"
3. Click **Create** → **Build your own template in the editor**
4. Copy and paste the contents of `deploy-arm-template.json`
5. Click **Save**
6. Fill in the parameters:
   - **Workspace Name**: Your Log Analytics/Sentinel workspace name
   - **Location**: Same region as your workspace
7. Click **Review + create** → **Create**

**⏱️ Wait for deployment to complete** (typically 2-5 minutes)

### Step 4: Capture Deployment Outputs

After the ARM template deploys successfully, capture the output values:

#### Using Azure CLI:

```bash
az deployment group show \
  --resource-group <your-resource-group-name> \
  --name deploy-arm-template \
  --query properties.outputs
```

#### Using PowerShell:

```powershell
$deployment = Get-AzResourceGroupDeployment `
  -ResourceGroupName <your-resource-group-name> `
  -Name deploy-arm-template

$deployment.Outputs
```

#### Using Azure Portal:

1. Navigate to **Resource groups** → Your resource group → **Deployments**
2. Click on the deployment name (e.g., `deploy-arm-template`)
3. Click **Outputs** in the left menu
4. **Copy these values:**
   - `dataCollectionEndpointUrl` → This is your **DCE_ENDPOINT**
   - `dataCollectionRuleImmutableId` → This is your **DCR_ID**
   - `streamName` → This is your **STREAM_NAME** (should be `Custom-TestData_CL`)

### Step 5: Grant App Registration Permissions

The App Registration (Service Principal) needs the **Monitoring Metrics Publisher** role on the Data Collection Rule. This allows the application to send data to the DCR.

> **Important:** You'll need the **Application (client) ID** from Step 2 and the **App Registration name** (e.g., `SentinelTestIngestion`) to assign permissions.

#### Using Azure CLI:

```bash
# Get the DCR Resource ID from deployment outputs
DCR_RESOURCE_ID=$(az deployment group show \
  --resource-group <your-resource-group-name> \
  --name deploy-arm-template \
  --query properties.outputs.dataCollectionRuleId.value -o tsv)

# Assign the Monitoring Metrics Publisher role to the Service Principal
# Replace <your-app-client-id> with the Application (client) ID from Step 2
az role assignment create \
  --assignee <your-app-client-id> \
  --role "Monitoring Metrics Publisher" \
  --scope $DCR_RESOURCE_ID
```

#### Using PowerShell:

```powershell
$deployment = Get-AzResourceGroupDeployment `
  -ResourceGroupName <your-resource-group-name> `
  -Name deploy-arm-template

$dcrId = $deployment.Outputs.dataCollectionRuleId.Value

# Assign the Monitoring Metrics Publisher role to the Service Principal
# Replace <your-app-client-id> with the Application (client) ID from Step 2
New-AzRoleAssignment `
  -ApplicationId <your-app-client-id> `
  -RoleDefinitionName "Monitoring Metrics Publisher" `
  -Scope $dcrId
```

#### Using Azure Portal:

1. Navigate to **Monitor** → **Data Collection Rules**
2. Find and click on **TestDataDCR** (the DCR created by the ARM template)
3. Click **Access control (IAM)** in the left menu
4. Click **+ Add** → **Add role assignment**
5. Search for and select **Monitoring Metrics Publisher**
6. Click **Next**
7. Click **+ Select members**
8. Search for your **App Registration name** (e.g., `SentinelTestIngestion`)
   - You can also search by the **Application (client) ID** from Step 2
9. Select it and click **Select**
10. Click **Review + assign** → **Review + assign**

**⏱️ Wait 2-3 minutes** for role assignment to propagate

> **Verification:** To verify the role was assigned correctly:
> - In the DCR, go to **Access control (IAM)** → **Role assignments**
> - Look for your App Registration name under the **Monitoring Metrics Publisher** role

### Step 6: Install Python Dependencies

```bash
pip install azure-identity azure-monitor-ingestion
```

### Step 7: Configure the Python Script

Open `test_sentinel_ingestion.py` and fill in the configuration variables at the top:

```python
# Azure AD App Registration credentials
TENANT_ID = "<your-tenant-id>"          # From Step 2
CLIENT_ID = "<your-client-id>"          # From Step 2
CLIENT_SECRET = "<your-client-secret>"  # From Step 2

# Data Collection Endpoint and Rule
DCE_ENDPOINT = "<dce-endpoint-url>"     # From Step 4 outputs
DCR_ID = "<dcr-immutable-id>"           # From Step 4 outputs
STREAM_NAME = "Custom-TestData_CL"      # From Step 4 outputs
```

### Step 8: Run the Ingestion Script

```bash
python test_sentinel_ingestion.py
```

**Expected output:**

```
======================================================================
Microsoft Sentinel Test Data Ingestion Script
Using Azure Monitor Ingestion API (DCE/DCR)
======================================================================

Configuration:
  Tenant ID: 3474cd6c-...
  Client ID: 29ea01f1-...
  DCE Endpoint: https://testdata-dce-kgq3.eastus-1.ingest.monitor.azure.com
  DCR ID: dcr-d19fbcaf984a4989beb027e6a15d818a
  Stream Name: Custom-TestData_CL
  Records to send: 3

Sample data to be sent:
[
  {
    "TimeGenerated": "2026-01-26T20:30:15Z",
    "EventType": "Test",
    "Message": "This is a test message from Python script",
    ...
  }
]

======================================================================
Authenticating with Azure...
✓ Authentication successful

Creating ingestion client...
✓ Client created successfully

Sending 3 records to Microsoft Sentinel...

======================================================================
✓ SUCCESS! Data has been ingested.
  Records sent: 3
  Response: HTTP 204 No Content (success)
  Timestamp: 2026-01-26 20:30:15 UTC

To query your data in Sentinel, use this KQL query:
  TestData_CL | take 10

Note: It may take 5-10 minutes for data to appear in Sentinel
======================================================================
```

### Step 9: Query the Data in Sentinel

**⏱️ Wait 5-20 minutes** for data to be indexed and become queryable.

1. Navigate to **Microsoft Sentinel** → Your workspace → **Logs**
2. Run the following KQL query:

```kql
TestData_CL
| take 3
```

**Expected results:**

| TimeGenerated | EventType | Message | Severity | Source | CustomField1 | CustomField2 |
|--------------|-----------|---------|----------|--------|--------------|--------------|
| 2026-01-26 20:30:15 | Test | This is a test message... | Informational | TestScript | Value1 | 12345 |
| 2026-01-26 20:30:15 | Alert | This is a test alert... | Medium | TestScript | Value2 | 67890 |
| 2026-01-26 20:30:15 | Info | Another test message... | Low | TestScript | Value3 | 99999 |

## 📊 Data Schema

The test data includes the following fields:

| Field Name | Type | Description |
|------------|------|-------------|
| **TimeGenerated** | datetime | The timestamp when the data was ingested |
| **EventType** | string | Type of event (Test, Alert, Info, etc.) |
| **Message** | string | Event message or description |
| **Severity** | string | Event severity (Informational, Low, Medium, High, Critical) |
| **Source** | string | Source of the event data |
| **CustomField1** | string | Custom field for additional string data |
| **CustomField2** | int | Custom field for additional numeric data |

## 🔧 Troubleshooting

### Authentication Errors

**Problem:** `ClientAuthenticationError` or `401 Unauthorized`

**Solution:**
- Verify your `TENANT_ID`, `CLIENT_ID`, and `CLIENT_SECRET` are correct
- Ensure the App Registration secret hasn't expired
- Check that you copied the secret value (not the secret ID)

### Permission Errors

**Problem:** `403 Forbidden` or `Insufficient permissions`

**Solution:**
- Verify the App Registration has the **Monitoring Metrics Publisher** role on the DCR
- Wait 2-3 minutes after role assignment for propagation
- Check role assignment in Azure Portal: DCR → Access control (IAM)

### Configuration Errors

**Problem:** `404 Not Found` or `InvalidDataCollectionRule`

**Solution:**
- Ensure `DCE_ENDPOINT` is the full URL (starts with `https://`)
- Verify `DCR_ID` is the **immutableId** (starts with `dcr-`), not the resource ID
- Check `STREAM_NAME` exactly matches `Custom-TestData_CL`

### Data Not Appearing

**Problem:** Script succeeds but no data in Sentinel

**Solution:**
- Wait longer - indexing can take up to 20 minutes
- Verify the table was created: Navigate to **Sentinel** → **Settings** → **Workspace settings** → **Tables**
- Check for `TestData_CL` in the tables list
- Verify the DCR dataFlow is configured correctly in Azure Portal

### Python Module Errors

**Problem:** `ModuleNotFoundError: No module named 'azure.monitor'`

**Solution:**
```bash
pip install azure-identity azure-monitor-ingestion
```

Or if using a virtual environment:
```bash
python -m pip install azure-identity azure-monitor-ingestion
```

## 🎨 Customization

To modify the data structure:

1. Update the `sample_data` list in `test_sentinel_ingestion.py`
2. Update column definitions in `table.json`
3. Update stream declaration in `dcr.json`
4. Update the table schema in `deploy-arm-template.json`
5. Redeploy the ARM template

Example: Adding a new field

```python
# In test_sentinel_ingestion.py
sample_data = [
    {
        "TimeGenerated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "EventType": "Test",
        "Message": "Test message",
        "Severity": "Low",
        "Source": "TestScript",
        "CustomField1": "Value1",
        "CustomField2": 12345,
        "NewField": "NewValue"  # Add your new field
    }
]
```

Then update the ARM template to include the new column in the schema.

## 🧹 Clean Up

To remove the test resources:

### Delete the Data Collection Rule

```bash
az monitor data-collection rule delete \
  --name TestDataDCR \
  --resource-group <your-resource-group-name>
```

### Delete the Data Collection Endpoint

```bash
az monitor data-collection endpoint delete \
  --name testdata-dce \
  --resource-group <your-resource-group-name>
```

### Note on Custom Tables

⚠️ **Custom log tables cannot be deleted** - they will remain in your workspace but won't incur costs unless data is being ingested.

### Delete App Registration (Optional)

1. Navigate to **Azure Portal** → **Azure Active Directory** → **App registrations**
2. Find your app registration
3. Click **Delete**

## 📚 Additional Resources

- [Azure Monitor Ingestion API Documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-ingestion-api-overview)
- [Data Collection Rules Overview](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/data-collection-rule-overview)
- [Microsoft Sentinel Custom Logs](https://learn.microsoft.com/en-us/azure/sentinel/connect-custom-logs)
- [Azure Monitor Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/monitor-ingestion-readme)

## 🤝 Contributing

This is part of the Azure-Sentinel repository. For contributions, please follow the main repository guidelines.

## 📝 License

This project is part of the Azure-Sentinel repository and follows the same license terms.

## ⚠️ Security Notice

**Never commit secrets to source control!**

The `test_sentinel_ingestion.py` file contains placeholder values for secrets. When using this in production:
- Use Azure Key Vault to store secrets
- Use environment variables
- Use managed identities where possible
- Rotate secrets regularly

## 💡 Support

For issues or questions:
- Check the [Troubleshooting](#-troubleshooting) section above
- Review Azure Monitor Ingestion API logs in Azure Portal
- Check Microsoft Sentinel documentation
- Open an issue in the Azure-Sentinel GitHub repository

