"""
Quick test script to verify Azure SQL Database connection
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Check if password is set
conn_str = os.getenv('MSSQL_CONNECTION_STRING', '')
if '{your_password}' in conn_str:
    print("[ERROR] You need to replace {your_password} in .env file")
    print("\nEdit .env and replace {your_password} with your actual Azure SQL password")
    exit(1)

print("Testing Azure SQL Database connection...")
print("=" * 60)

try:
    from integrations.mssql import check_database_health

    health = check_database_health()

    if health.get('status') == 'healthy':
        print("[SUCCESS] Connection successful!")
        print(f"\nDatabase: RBF_Brain_Server")
        print(f"Industries: {health.get('industries', 0)}")
        print(f"Pricing factors: {health.get('pricing_factors', 0)}")
        print(f"Applications: {health.get('applications', 0)}")
        print("\n[READY] Run migration: python scripts/run_migration.py")
    else:
        print(f"[WARNING] Connection issue: {health.get('error', 'Unknown')}")

except Exception as e:
    print(f"[FAILED] Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check password in .env is correct")
    print("2. Check firewall rules in Azure Portal allow your IP")
    print("3. Verify database name is 'RBF_Brain_Server'")
