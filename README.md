# Access Token Refresh with Entra ID for Azure Database for PostgreSQL

This repository provides sample implementations in Python and .NET for refreshing access tokens using Microsoft Entra ID (formerly Azure AD), while connecting to Azure Database for PostgreSQL.

## Table of Contents
- [Overview](#overview)
- [Python Usage](#python-usage)
- [Dotnet Usage](#dotnet-usage)

## Overview
Access tokens are essential for securely accessing protected resources in Microsoft Entra ID. However, since they expire after a set duration, applications need a reliable refresh mechanism to maintain seamless authentication without interrupting the user experience.
To support this, we’ve created extension methods for both Npgsql (for .NET) and psycopg (for Python). These methods can be easily invoked in your application code to handle token refresh logic, making it simpler to maintain secure and uninterrupted database connections.

## Python Usage

Note: this section covers two related but different scenarios — running the included sample, and reusing the sample code in your own project. Running the sample (see the "Prerequisites" below) requires installing the dependencies in `python/requirements.txt` and optionally using the `.env` file in the `python/` folder. If instead you are copying the sample code into your own project, you only need the parts you use (for example `entra_connection.py`) and you may obtain connection details however your application does (configuration service, secrets manager, environment variables, etc.).

When reusing the code, import the `AsyncEntraConnection` class and pass it as the `connection_class` when creating a `psycopg_pool.AsyncConnectionPool`. Example:

```python
from entra_connection import AsyncEntraConnection
from psycopg_pool import AsyncConnectionPool

pool = AsyncConnectionPool(
  min_size=1,
  max_size=10,
  connection_class=AsyncEntraConnection,
  kwargs=dict(host="your-host", dbname="your-db", sslmode="require"),
)
```

See `python/sample.py` for a complete runnable example that shows how the sample wires up `AsyncEntraConnection` and loads configuration from `.env` for demo purposes.

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

### How Token refresh works (Python)

This repository provides an `AsyncEntraConnection` class (see `python/entra_connection.py`) that encapsulates Entra ID token acquisition and uses the token as the database password for each connection.

Key points:

- psycopg's connection pools accept a `connection_class` parameter. Passing `AsyncEntraConnection` lets you override how connections are created and authenticated so the pool transparently uses Entra ID tokens instead of a static password.
- `AsyncEntraConnection` uses an Azure Identity `TokenCredential` (by default `DefaultAzureCredential`) to request access tokens scoped for Azure Database for PostgreSQL. Tokens are acquired asynchronously and injected into the connection handshake as the password.
- The class also parses token claims when necessary to determine the correct database username (for example, from `upn` or `preferred_username`) if a username isn't provided in the connection kwargs.
- Because tokens expire, the connection class fetches a fresh token on demand (for each new connection or when the pool re-creates connections), avoiding the need for separate refresh threads.

Minimal usage example (repeated here for clarity):

```python
from entra_connection import AsyncEntraConnection
from psycopg_pool import AsyncConnectionPool

pool = AsyncConnectionPool(
    min_size=1,
    max_size=10,
    connection_class=AsyncEntraConnection,
    kwargs=dict(host="your-host", dbname="your-db", sslmode="require"),
)
```

Use `python/sample.py` as a runnable demo that shows loading configuration from `.env` and creating the pool. If you copy `AsyncEntraConnection` into your own project you don't need the sample's `.env` or exact runtime layout — just supply host/DB settings however your application normally gets configuration.


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
  dotnet run --project PGEntraExamples.csproj -f net8.0

  # Or run for .NET 9.0
  dotnet run --project PGEntraExamples.csproj -f net9.0

  # Or (if built with .NET 10 SDK) run for .NET 10.0
  dotnet run --project PGEntraExamples.csproj -f net10.0
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
