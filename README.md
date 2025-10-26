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

This repository provides Entra ID authentication samples for three popular Python PostgreSQL libraries:

- **psycopg2** - Legacy psycopg library (synchronous only)
- **psycopg3** - Modern psycopg library with both synchronous and asynchronous support
- **SQLAlchemy** - High-level ORM/database toolkit with both synchronous and asynchronous support

Each implementation is located in its respective folder under `python/` with its own `entra_connection.py` and `sample.py` files.

Note: This section covers two related scenarios — running the included samples, and reusing the sample code in your own project. Running the samples requires installing all dependencies in `python/requirements.txt` and using the `.env` file in the `python/` folder. If you're copying sample code into your own project, you only need the parts you use (for example, just the `psycopg3/entra_connection.py` file) and can obtain connection details however your application does (configuration service, secrets manager, environment variables, etc.).

### Prerequisites
- Python 3.8+
- Install dependencies:
  ```powershell
  cd python
  pip install -r requirements.txt
  ```

### Environment Variables (.env)

Create a `.env` file in the `python` folder with your database connection details:

```env
HOSTNAME=<your-db-hostname>
DATABASE=<your-db-name>
```

Make sure to add `.env` to your `.gitignore` file to avoid committing secrets to source control.

### psycopg2 Usage

For legacy applications using psycopg2 (synchronous only):

```python
from psycopg2.entra_connection import EntraConnection
from psycopg2.extensions import connection

# Use EntraConnection as your connection class
conn = EntraConnection.connect(
    host="your-host",
    dbname="your-db",
    sslmode="require"
)
```

Run the sample:
```powershell
cd python
python psycopg2/sample.py
```

### psycopg3 Usage

For modern applications using psycopg3, which supports both synchronous and asynchronous connections:

**Synchronous Example:**
```python
from psycopg3.entra_connection import EntraConnection
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    conninfo=f"postgresql://{hostname}:5432/{database}",
    min_size=1,
    max_size=5,
    connection_class=EntraConnection,
)
```

**Asynchronous Example:**
```python
from psycopg3.async_entra_connection import AsyncEntraConnection
from psycopg_pool import AsyncConnectionPool

pool = AsyncConnectionPool(
    conninfo=f"postgresql://{hostname}:5432/{database}",
    min_size=1,
    max_size=5,
    connection_class=AsyncEntraConnection,
)
```

Run the sample:
```powershell
cd python
# Run both sync and async examples
python psycopg3/sample.py

# Or run only sync
python psycopg3/sample.py --mode sync

# Or run only async
python psycopg3/sample.py --mode async
```

See `python/psycopg3/sample.py` for complete runnable examples.

### SQLAlchemy Usage

For applications using SQLAlchemy ORM, which supports both synchronous and asynchronous engines:

**Synchronous Example:**
```python
from sqlalchemy import create_engine
from sqlalchemy.entra_connection import enable_entra_authentication

engine = create_engine(f"postgresql+psycopg://{hostname}:5432/{database}")
enable_entra_authentication(engine)
```

**Asynchronous Example:**
```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.async_entra_connection import enable_entra_authentication_async

engine = create_async_engine(f"postgresql+psycopg://{hostname}:5432/{database}")
enable_entra_authentication_async(engine)
```

Run the sample:
```powershell
cd python
# Run both sync and async examples
python sqlalchemy/sample.py

# Or run only sync
python sqlalchemy/sample.py --mode sync

# Or run only async
python sqlalchemy/sample.py --mode async
```

See `python/sqlalchemy/sample.py` for complete runnable examples.

### How Token Refresh Works (Python)

All three Python implementations use Azure Identity's `TokenCredential` (by default `DefaultAzureCredential`) to acquire Entra ID access tokens scoped for Azure Database for PostgreSQL. The tokens are used as the database password for authentication.

#### psycopg2 Implementation

The `EntraConnection` class extends psycopg2's `connection` class:

- Overrides the `connect()` method to fetch Entra ID tokens before establishing the connection
- Uses synchronous token acquisition via `get_entra_conninfo()`
- Parses token claims to extract the database username from `upn`, `preferred_username`, or other claims
- Each new connection automatically gets a fresh token

#### psycopg3 Implementation

psycopg3 provides both synchronous and asynchronous connection classes:

- **`EntraConnection`**: Synchronous connections using `get_entra_conninfo()`
- **`AsyncEntraConnection`**: Asynchronous connections using `get_entra_conninfo_async()`
- Both classes integrate with psycopg's connection pools via the `connection_class` parameter
- Tokens are acquired on-demand for each new connection, avoiding separate refresh threads
- Username extraction follows the same claim hierarchy as psycopg2

#### SQLAlchemy Implementation

SQLAlchemy uses event listeners to inject Entra authentication:

- **`enable_entra_authentication(engine)`**: For synchronous SQLAlchemy engines
- **`enable_entra_authentication_async(engine)`**: For asynchronous SQLAlchemy engines
- Registers a `do_connect` event handler that runs before each connection is established
- The event handler fetches fresh tokens and injects them as connection parameters
- Works with any SQLAlchemy-compatible PostgreSQL driver (uses psycopg by default)

**Key Benefits Across All Implementations:**

- Automatic token refresh on each connection (tokens expire after ~1 hour)
- No manual token management or refresh threads required
- Seamless integration with connection pooling
- Works with `DefaultAzureCredential` for automatic credential discovery (Managed Identity, Azure CLI, etc.)

Example token refresh flow:

1. Application requests a database connection from the pool
2. The custom connection class or event handler intercepts the connection creation
3. A fresh Entra ID token is requested from Azure Identity
4. The token is used as the password for PostgreSQL authentication
5. Connection is established and returned to the application


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
