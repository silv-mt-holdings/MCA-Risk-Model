# ODBC Driver Setup for SQL Server

## Overview

The Risk-Model-01 project uses `pymssql` to connect to Azure SQL Database. While `pip install pymssql` installs the Python library, it **requires system-level ODBC drivers** to actually connect to SQL Server.

---

## Already Installed?

Check if drivers are already installed:

**Windows:**
```bash
# Check registry
reg query "HKLM\SOFTWARE\Microsoft\ODBC Drivers"

# Or check via ODBC Data Source Administrator
odbcad32.exe
```

**Linux:**
```bash
odbcinst -q -d
```

If you see "ODBC Driver 17 for SQL Server" or "ODBC Driver 18 for SQL Server", you're good!

---

## Installation

### Windows

ODBC drivers are usually pre-installed on Windows. If not:

1. Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
2. Install "ODBC Driver 18 for SQL Server"
3. Restart terminal

### Ubuntu/Debian

```bash
# Add Microsoft repository
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

# Install driver
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Install unixODBC (required)
sudo apt-get install -y unixodbc-dev
```

### macOS

```bash
# Using Homebrew
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18 mssql-tools18
```

### Docker (Debian-based)

Add to your `Dockerfile`:

```dockerfile
# Install ODBC Driver for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev && \
    apt-get clean
```

---

## Verification

Test the connection:

```bash
python test_connection.py
```

Expected output:
```
[SUCCESS] Connection successful!
Database: RBF_Brain_Server
Industries: 1086
```

---

## Troubleshooting

### Error: "Can't open lib 'ODBC Driver 17'"

**Solution:** Install ODBC Driver (see above)

### Error: "Data source name not found"

**Solution:** Check connection string format:
```python
MSSQL_CONNECTION_STRING=Server=server.database.windows.net;Database=dbname;User=user;Password=pass;Encrypt=true
```

### Error: "SSL connection error"

**Solution:** Add `TrustServerCertificate=yes` to connection string (development only):
```python
MSSQL_CONNECTION_STRING=Server=...;TrustServerCertificate=yes
```

### Error: "Login timeout expired"

**Solutions:**
1. Check firewall rules in Azure Portal
2. Verify server name is correct
3. Check your internet connection
4. Try increasing timeout in connection string: `Connection Timeout=30`

---

## Alternative: Using `pyodbc` Instead of `pymssql`

If you prefer `pyodbc` (more feature-rich but requires ODBC drivers):

**Update requirements.txt:**
```txt
# Replace pymssql with:
pyodbc==5.0.1
```

**Update integrations/mssql.py:**
```python
import pyodbc

# Change connection to:
conn = pyodbc.connect(
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server={server};Database={database};"
    f"Uid={user};Pwd={password};"
    f"Encrypt=yes;TrustServerCertificate=no"
)
```

---

## Production Deployment

### Azure App Service

✅ **ODBC drivers pre-installed** - no action needed

### Azure Container Instances

Add to Dockerfile (see Docker section above)

### AWS EC2 / Other VMs

Install drivers using platform-specific instructions above

### Railway / Render / Fly.io

Check platform documentation - may require custom buildpacks

---

## Current Configuration

Risk-Model-01 uses:
- **Library**: `pymssql` (FreeTDS-based, lighter than pyodbc)
- **Connection**: Azure SQL Database
- **Authentication**: SQL Authentication (username/password)
- **Encryption**: TLS 1.2+ required

**Connection string format:**
```
Server=rbf-brain-server.database.windows.net;
Database=RBF_Brain_Server;
User=sqladmin;
Password=YourPassword;
Encrypt=true
```

---

## References

- [Microsoft ODBC Driver Docs](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- [pymssql Documentation](https://pymssql.readthedocs.io/)
- [Azure SQL Connection Strings](https://learn.microsoft.com/en-us/azure/azure-sql/database/connect-query-python)

---

**Author**: IntensiveCapFi / Silv MT Holdings
**Version**: 1.0 - Risk-Model-01
**Date**: January 2026
