"""
Diagnose Azure SQL connection issues
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("Diagnosing Azure SQL Connection...")
print("=" * 60)

# Get connection string
conn_str = os.getenv('MSSQL_CONNECTION_STRING', '')
print(f"Connection string loaded: {bool(conn_str)}")

# Parse connection details
if conn_str:
    parts = dict(item.split('=', 1) for item in conn_str.split(';') if '=' in item)
    server = parts.get('Server', 'unknown')
    database = parts.get('Database', 'unknown')
    user = parts.get('User', 'unknown')

    print(f"Server: {server}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print(f"Password set: {bool(parts.get('Password'))}")
    print()

# Test 1: Try connecting to master database (to test firewall/auth)
print("Test 1: Connecting to 'master' database (firewall test)...")
print("-" * 60)

try:
    import pymssql

    # Parse connection for master
    master_conn = pymssql.connect(
        server=parts.get('Server', ''),
        database='master',  # Connect to master instead
        user=parts.get('User', ''),
        password=parts.get('Password', ''),
        timeout=30,
        login_timeout=30
    )

    print("[SUCCESS] Connected to master database!")
    print("Firewall and authentication are working.\n")

    # List databases
    cursor = master_conn.cursor()
    cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb')")
    databases = [row[0] for row in cursor.fetchall()]

    print(f"Found {len(databases)} user database(s):")
    for db in databases:
        print(f"  - {db}")

    master_conn.close()

    # Check if RBF_Brain_Server exists
    if database in databases:
        print(f"\n[OK] Database '{database}' exists!")
    else:
        print(f"\n[ISSUE] Database '{database}' NOT FOUND!")
        print(f"Available databases: {', '.join(databases)}")
        print(f"\nUpdate .env with correct database name.")

except pymssql.OperationalError as e:
    print(f"[FAILED] Cannot connect to master: {e}")
    print("\nLikely issues:")
    print("1. Firewall rule not set (add your IP in Azure Portal)")
    print("2. Password incorrect")
    print("3. Server name wrong")

except Exception as e:
    print(f"[ERROR] {e}")

print()

# Test 2: Try connecting to target database
print("Test 2: Connecting to target database...")
print("-" * 60)

try:
    import pymssql

    target_conn = pymssql.connect(
        server=parts.get('Server', ''),
        database=parts.get('Database', ''),
        user=parts.get('User', ''),
        password=parts.get('Password', ''),
        timeout=30,
        login_timeout=30
    )

    print(f"[SUCCESS] Connected to '{database}'!")
    target_conn.close()
    print("\nEverything is working! Run: python scripts/run_migration.py")

except Exception as e:
    print(f"[FAILED] {e}")
    print("\nBased on Test 1 results, update database name in .env if needed.")
