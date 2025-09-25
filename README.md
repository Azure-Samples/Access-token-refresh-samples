# Access Token Refresh with Entra ID

This repository demonstrates how to implement samples for refreshing access tokens for Microsoft Entra ID (formerly Azure AD) in both Python and .NET.

## Table of Contents
- [Overview](#overview)
- [Python Usage](#python-usage)
- [Dotnet Usage](#dotnet-usage)
- [Configuration](#configuration)

## Overview
Access tokens are essential for securely accessing protected resources in Microsoft Entra ID. However, since they expire after a set duration, applications need a reliable refresh mechanism to maintain seamless authentication without interrupting the user experience.
To support this, we’ve created extension methods for both Npgsql (for .NET) and psycopg (for Python). These methods can be easily invoked in your application code to handle token refresh logic, making it simpler to maintain secure and uninterrupted database connections.

## Python Usage

### Prerequisites
- Python 3.8+
- Install dependencies:
  ```powershell
  cd python
  pip install -r requirements.txt
  ```

### Example Usage
1. Configure your hostname, databasename, username and password in the `.env` file.
2. Use the provided `entra_connection.py` to obtain and refresh tokens:
   ```python
   from entra_connection import get_token, refresh_token
   ```
3. See `sample.py` for a complete example.

### Environment Variables (.env)

You can store sensitive information such as hostname and database name in a `.env` file in the `python` folder. Example:

```env
HOSTNAME=<your-db-hostname>
DATABASE=<your-db-name>
```

Make sure to add `.env` to your `.gitignore` file to avoid committing secrets to source control.

#### Using .env in sample.py

To load environment variables in `sample.py`, you can use the `os` module:

```python
import os
# If using python-dotenv, uncomment below:
# from dotenv import load_dotenv; load_dotenv()

hostname = os.getenv("HOSTNAME")
database = os.getenv("DATABASE")
```

For automatic loading from `.env`, install `python-dotenv` and uncomment the relevant line above.

### How Token Refresh is Implemented in Python

The Python implementation uses `psycopg3` and Azure Identity libraries to enable Entra ID authentication for PostgreSQL connections. Here’s how it works:

- **Async Token Acquisition:**
  - Uses Azure Identity’s `DefaultAzureCredential` to acquire access tokens for Entra-ID in Azure Database for PostgreSQL.
  - The token is fetched asynchronously to avoid blocking the event loop, making it suitable for async applications.
- **Connection Pool Integration:**
  - Integrates with `psycopg_pool.AsyncConnectionPool` to provide tokens as passwords for each connection.
  - Ensures each connection uses a fresh, valid token by acquiring it on demand.
- **Username Extraction:**
  - Extracts the username from the token claims, to set the correct database user.
- **Sample Usage:**
  - The `sample.py` file demonstrates how to set up the async connection pool and use Entra ID tokens for authentication.

This design provides secure, scalable, and non-blocking authentication for PostgreSQL in Python applications using Entra ID.

## Dotnet Usage

### Prerequisites
- .NET 8.0 or 9.0 SDK installed
  - Optional: .NET 10.0 SDK if you want to build/run for `net10.0`
- Npgsql (for PostgreSQL integration, if needed)

### Example Usage
1. Copy `appsettings.example.json` to `appsettings.json` and fill in your credentials:
   ```json
   {
    "Host": "<your-server-host-name>",
    "Database": "<your-database>",
    "Port": 5432,
    "SslMode": "Require"
   }
   ```
2. Build the project:

  ```powershell
  cd dotnet
  # Build for default frameworks (net8.0 and net9.0)
  dotnet build

  # Optionally include net10.0 (requires .NET 10 SDK):
  dotnet build -p:IncludeNet10=true
  ```
3. Run the sample:

  ```powershell
  # Run for .NET 8.0
  dotnet run --project PGSKExamples.csproj -f net8.0

  # Or run for .NET 9.0
  dotnet run --project PGSKExamples.csproj -f net9.0

  # Or (if built with .NET 10 SDK) run for .NET 10.0
  dotnet run --project PGSKExamples.csproj -f net10.0
  ```
4. Use the logic in `NpgsqlDataSourceBuilderExtensions.cs` and `sample.cs` to handle token refresh.

### Environment Variables (.env)

You can also use environment variables instead of or alongside `appsettings.json`:

```powershell
# Set environment variables (PowerShell)
$env:Host = "your-server.postgres.database.azure.com"
$env:Database = "mydatabase"
$env:Port = "5432"
$env:SslMode = "Require"

# Then run the sample
dotnet run
```

```bash
# Or in bash/Linux
export Host="your-server.postgres.database.azure.com"
export Database="mydatabase"
export Port="5432"
export SslMode="Require"

dotnet run
```

The sample will automatically read from both `appsettings.json` and environment variables, with environment variables taking precedence.

### How Token Refresh is Implemented in .NET

The extension method `UseEntraAuthentication` for `NpgsqlDataSourceBuilder` configures PostgreSQL connections to use Entra ID authentication. Here’s how it works:

- **Token Acquisition:**
  - Uses `TokenCredential` (defaulting to `DefaultAzureCredential`) to acquire an access token for Azure DB for PostgreSQL.
  - If the connection string does not specify a username, it extracts the username from the token claims (`upn`, `preferred_username`, or `unique_name`).
- **Password Provider:**
  - Sets a password provider on the builder that fetches a fresh token each time a password is needed, ensuring the token is always valid.
  - Supports both synchronous and asynchronous token acquisition via `GetToken` and `GetTokenAsync`.
- **Async Support:**
  - The async extension `UseEntraAuthenticationAsync` allows for non-blocking token acquisition and connection setup, ideal for scalable applications.
- **JWT Parsing:**
  - Decodes the JWT token payload to extract the username claim, handling base64 padding and JSON parsing.

This approach ensures secure, up-to-date authentication for every database connection, with minimal configuration required by the user.

## Next Steps
For further details, see the code comments and sample files in each language folder.
