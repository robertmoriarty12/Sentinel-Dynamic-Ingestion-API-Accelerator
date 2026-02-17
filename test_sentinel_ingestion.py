"""
Simple test script to push JSON data to Microsoft Sentinel using Monitor Ingestion API
This script demonstrates basic data ingestion for testing purposes using DCE/DCR.
"""

from datetime import datetime
from azure.identity import ClientSecretCredential
from azure.monitor.ingestion import LogsIngestionClient
from azure.core.exceptions import HttpResponseError

# ============================================================================
# CUSTOMER CONFIGURATION - Fill in these variables
# ============================================================================

# Azure AD App Registration credentials
TENANT_ID = ""          # Your Azure AD Tenant ID
CLIENT_ID = ""          # Your App Registration Client ID
CLIENT_SECRET = ""      # Your App Registration Client Secret

# Data Collection Endpoint and Rule
DCE_ENDPOINT = ""       # Data Collection Endpoint URL (e.g., https://my-dce-abcd.eastus-1.ingest.monitor.azure.com)
DCR_ID = ""            # Data Collection Rule immutableId (dcr-xxxxxxxxxxxxx)
STREAM_NAME = "Custom-TestData_CL"       # Stream name from DCR (e.g., Custom-MyTable_CL)




# ============================================================================
# Sample JSON Data to Push
# ============================================================================

# Simple test data - customize this as needed
sample_data = [
    {
        "TimeGenerated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "RawData": {
            "SchemaType": "UserLogin",
            "UserId": "user123",
            "Action": "Login",
            "Details": {
                "IP": "192.168.1.1",
                "Success": True
            }
        }
    },
    {
        "TimeGenerated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "RawData": {
            "SchemaType": "FileAccess",
            "FileName": "secret.txt",
            "Operation": "Read",
            "Size": 1024
        }
    }
]

# ============================================================================
# Main execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Microsoft Sentinel Test Data Ingestion Script")
    print("Using Azure Monitor Ingestion API (DCE/DCR)")
    print("=" * 70)
    
    # Validate configuration
    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET, DCE_ENDPOINT, DCR_ID, STREAM_NAME]):
        print("\n✗ ERROR: Please configure all required variables:")
        print("  - TENANT_ID")
        print("  - CLIENT_ID") 
        print("  - CLIENT_SECRET")
        print("  - DCE_ENDPOINT")
        print("  - DCR_ID")
        print("  - STREAM_NAME")
        print("\nFind these values in Azure Portal:")
        print("  - App Registration for credentials")
        print("  - Monitor > Data Collection Endpoints for DCE")
        print("  - Monitor > Data Collection Rules for DCR and Stream")
        exit(1)
    
    print(f"\nConfiguration:")
    print(f"  Tenant ID: {TENANT_ID}")
    print(f"  Client ID: {CLIENT_ID}")
    print(f"  DCE Endpoint: {DCE_ENDPOINT}")
    print(f"  DCR ID: {DCR_ID}")
    print(f"  Stream Name: {STREAM_NAME}")
    print(f"  Records to send: {len(sample_data)}")
    
    print(f"\nSample data to be sent:")
    import json
    print(json.dumps(sample_data, indent=2))
    
    print(f"\n{'='*70}")
    print("Authenticating with Azure...")
    
    try:
        # Step 1: Authenticate with Azure
        credential = ClientSecretCredential(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        print("✓ Authentication successful")
        
        # Step 2: Create ingestion client
        print("\nCreating ingestion client...")
        client = LogsIngestionClient(
            endpoint=DCE_ENDPOINT,
            credential=credential,
            logging_enable=True
        )
        print("✓ Client created successfully")
        
        # Step 3: Send data to Sentinel
        print(f"\nSending {len(sample_data)} records to Microsoft Sentinel...")
        response = client.upload(
            rule_id=DCR_ID,
            stream_name=STREAM_NAME,
            logs=sample_data
        )
        
        print("\n" + "=" * 70)
        print("✓ SUCCESS! Data has been ingested.")
        print(f"  Records sent: {len(sample_data)}")
        print(f"  Response: {response if response else 'HTTP 204 No Content (success)'}")
        print(f"  Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        print(f"\nTo query your data in Sentinel, use this KQL query:")
        # Extract table name from stream name (remove Custom- prefix and _CL suffix if present)
        table_name = STREAM_NAME.replace("Custom-", "").replace("_CL", "")
        print(f"  {table_name} | take 10")
        print(f"\nNote: It may take 5-10 minutes for data to appear in Sentinel")
        print("=" * 70)
        
    except HttpResponseError as e:
        print("\n" + "=" * 70)
        print("✗ FAILED! Azure API Error:")
        print(f"  {str(e)}")
        print("\nPlease check:")
        print("  1. App Registration has 'Monitoring Metrics Publisher' role on DCR")
        print("  2. DCE endpoint URL is correct")
        print("  3. DCR immutableId is correct")
        print("  4. Stream name matches DCR configuration")
        print("=" * 70)
        exit(1)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("✗ FAILED! Unexpected error:")
        print(f"  {str(e)}")
        print("=" * 70)
        exit(1)
