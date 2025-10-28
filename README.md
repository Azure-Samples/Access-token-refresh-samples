# Access Token Refresh with Entra ID for Azure Database for PostgreSQL

This repository provides sample implementations in Python, JavaScript, and .NET for refreshing access tokens using Microsoft Entra ID (formerly Azure AD), while connecting to Azure Database for PostgreSQL.

## Table of Contents
- [Overview](#overview)
- [Python Usage](#python-usage)
- [Java Usage](#java-usage)
- [JavaScript Usage](#javascript-usage)
- [Dotnet Usage](#dotnet-usage)

## Overview
Access tokens are essential for securely accessing protected resources in Microsoft Entra ID. However, since they expire after a set duration, applications need a reliable refresh mechanism to maintain seamless authentication without interrupting the user experience.
To support this, we've created extension methods for Npgsql (for .NET), psycopg (for Python), and JDBC/Hibernate (for Java). These methods can be easily invoked in your application code to handle token refresh logic, making it simpler to maintain secure and uninterrupted database connections.

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

### Psycopg2 Usage

Run the sample:
```powershell
cd python
python psycopg2/sample.py
```

See `python/psycopg2/sample.py` for complete runnable examples.

### Psycopg3 Usage

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

### Using in Your Own Project

To integrate Entra ID authentication into your own Python project, follow these steps:

#### For psycopg2

1. **Copy the helper module:**
   
   Copy `python/psycopg2/entra_connection.py`, `python/shared.py`, and `python/errors.py` from this repository into your project.

2. **Install required dependencies:**
   
   ```bash
   pip install psycopg2-binary azure-identity
   ```

3. **Import and use in your code:**

   ```python
   from entra_connection import EntraConnection
   
   # Create a connection with Entra ID authentication
   conn = EntraConnection.connect(
       host='your-server.postgres.database.azure.com',
       dbname='your-database',
       sslmode='require'
   )
   
   # Use the connection
   with conn.cursor() as cur:
       cur.execute("SELECT current_user")
       print(cur.fetchone())
   
   conn.close()
   ```

#### For psycopg3

1. **Copy the helper modules:**
   
   Copy `python/psycopg3/entra_connection.py`, `python/psycopg3/async_entra_connection.py`, `python/shared.py`, and `python/errors.py` from this repository into your project.

2. **Install required dependencies:**
   
   ```bash
   pip install psycopg[binary] psycopg-pool azure-identity
   ```

3. **Import and use in your code:**

   **Synchronous:**
   ```python
   from entra_connection import EntraConnection
   from psycopg_pool import ConnectionPool
   
   pool = ConnectionPool(
       conninfo="postgresql://your-server.postgres.database.azure.com:5432/your-database",
       min_size=1,
       max_size=5,
       connection_class=EntraConnection,
       kwargs=dict(sslmode="require")
   )
   
   # Use the pool
   with pool.connection() as conn:
       with conn.cursor() as cur:
           cur.execute("SELECT current_user")
           print(cur.fetchone())
   ```

   **Asynchronous:**
   ```python
   import asyncio
   from async_entra_connection import AsyncEntraConnection
   from psycopg_pool import AsyncConnectionPool
   
   async def main():
       pool = AsyncConnectionPool(
           conninfo="postgresql://your-server.postgres.database.azure.com:5432/your-database",
           min_size=1,
           max_size=5,
           connection_class=AsyncEntraConnection,
           kwargs=dict(sslmode="require")
       )
       
       async with pool.connection() as conn:
           async with conn.cursor() as cur:
               await cur.execute("SELECT current_user")
               print(await cur.fetchone())
       
       await pool.close()
   
   asyncio.run(main())
   ```

#### For SQLAlchemy

1. **Copy the helper modules:**
   
   Copy `python/sqlalchemy/entra_connection.py`, `python/sqlalchemy/async_entra_connection.py`, `python/shared.py`, and `python/errors.py` from this repository into your project.

2. **Install required dependencies:**
   
   ```bash
   pip install sqlalchemy psycopg[binary] azure-identity
   ```

3. **Import and use in your code:**

   **Synchronous:**
   ```python
   from sqlalchemy import create_engine, text
   from entra_connection import enable_entra_authentication
   
   engine = create_engine("postgresql+psycopg://your-server.postgres.database.azure.com:5432/your-database")
   enable_entra_authentication(engine)
   
   # Use the engine
   with engine.connect() as conn:
       result = conn.execute(text("SELECT current_user"))
       print(result.fetchone())
   ```

   **Asynchronous:**
   ```python
   import asyncio
   from sqlalchemy.ext.asyncio import create_async_engine
   from sqlalchemy import text
   from async_entra_connection import enable_entra_authentication_async
   
   async def main():
       engine = create_async_engine("postgresql+psycopg://your-server.postgres.database.azure.com:5432/your-database")
       enable_entra_authentication_async(engine)
       
       async with engine.connect() as conn:
           result = await conn.execute(text("SELECT current_user"))
           print(result.fetchone())
       
       await engine.dispose()
   
   asyncio.run(main())
   ```

#### Configure Authentication

Ensure your application has access to Azure credentials through one of these methods:
- **Azure CLI**: Run `az login` before running your app
- **Environment variables**: Set `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`
- **Managed Identity**: When running on Azure (App Service, VM, Container Apps, etc.)
- **VS Code**: Sign in to Azure extension
- **Other**: Any method supported by `DefaultAzureCredential`

The helper modules handle token acquisition, automatic refresh, and username extraction from JWT claims. You don't need to modify them—just import and use as shown above.

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

## Java Usage

This repository provides Entra ID authentication samples for Java applications using PostgreSQL, with support for both plain JDBC and Hibernate ORM.

### Prerequisites
- Java 17 or higher
- Maven 3.6+ (for dependency management)
- Azure Identity Extensions library

### Setup

1. **Install Maven dependencies:**

   The project includes a `pom.xml` file with all required dependencies. Navigate to the `java` folder and run:

   ```powershell
   cd java
   mvn clean compile

2. **Configure database connection:**

   Create or edit `application.properties` in the `java` folder:

   ```properties
   url=jdbc:postgresql://<your-server>.postgres.database.azure.com:5432/<database>?sslmode=require&authenticationPluginClassName=com.azure.identity.extensions.jdbc.postgresql.AzurePostgresqlAuthenticationPlugin
   user=<your-username>@<your-domain>.onmicrosoft.com

### Running the Examples

The project includes two examples:
- `EntraIdExtensionJdbc.java` - Basic JDBC and HikariCP connection pooling
- `EntraIdExtensionHibernate.java` - Hibernate ORM with Entra ID authentication

**To switch between examples**, edit the `<mainClass>` property in `pom.xml`:

```xml
<plugin>
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>exec-maven-plugin</artifactId>
  <version>3.1.0</version>
  <configuration>
    <!-- Change this line to switch between examples -->
    <mainClass>EntraIdExtensionJdbc</mainClass>
    <!-- Or use: <mainClass>EntraIdExtensionHibernate</mainClass> -->
  </configuration>
</plugin>
```

Then run:
```powershell
cd java
mvn exec:java
```

**Note:** Do not use VS Code's "Run" button directly. Run examples through Maven to ensure proper classpath and resource loading.

### Using in Your Own Project

To integrate Entra ID authentication into your own Java project, you can follow the same setup steps for running the examples.

### How Token Refresh Works (Java)

The Azure Identity Extensions library (`azure-identity-extensions`) automatically handles token refresh:

1. **Authentication Plugin**: The JDBC URL includes `authenticationPluginClassName=com.azure.identity.extensions.jdbc.postgresql.AzurePostgresqlAuthenticationPlugin` which intercepts connection attempts.

2. **Token Acquisition**: The plugin uses `DefaultAzureCredential` to automatically acquire Entra ID access tokens scoped for Azure Database for PostgreSQL.

3. **Automatic Refresh**: 
   - For single connections: A fresh token is acquired for each connection
   - For connection pools: Tokens are refreshed automatically when connections are created or revalidated
   - The `maxLifetime` setting in HikariCP (30 minutes) ensures connections are recycled before token expiration

4. **Credential Discovery**: DefaultAzureCredential attempts authentication in this order:
   - Environment variables
   - Managed Identity
   - Azure CLI credentials
   - IntelliJ credentials
   - VS Code credentials
   - And more...

This design ensures tokens are always valid without manual refresh logic, and connection pools automatically handle token lifecycle.

## JavaScript Usage

This repository provides Entra ID authentication samples for JavaScript/Node.js applications using PostgreSQL, with support for both the `pg` (node-postgres) library and Sequelize ORM.

### Prerequisites
- Node.js 18+ (for ES modules support)
- npm or yarn package manager

### Setup

1. **Install dependencies:**

   Navigate to the `javascript` folder and install required packages:

   ```bash
   cd javascript
   npm install
   ```
   
2. **Configure database connection:**

   Create a `.env` file in the `javascript` folder:

   ```env
   PGHOST=<your-server>.postgres.database.azure.com
   PGPORT=5432
   PGDATABASE=<your-database>
   PGUSER=<your-username>@<your-domain>.onmicrosoft.com
   ```

   Replace:
   - `<your-server>` with your Azure PostgreSQL server hostname
   - `<database>` with your database name
   - `<your-database>` with your database name
   - `<your-username>@<your-domain>.onmicrosoft.com` with your Entra ID user principal name

### Running the Examples

**pg (node-postgres) Example:**
```bash
cd javascript
npm run pg
```

**Sequelize ORM Example:**
```bash
cd javascript
npm run sequelize
```

### Using in Your Own Project

To integrate Entra ID authentication into your own JavaScript/Node.js project, follow these steps:

1. **Copy the helper module:**
   
   Copy `javascript/entra-connection.js` from this repository into your project.

2. **Install required dependencies:**
   
   ```bash
   npm install pg sequelize @azure/identity
   ```
   
   Note: Install only the libraries you need (`pg` and/or `sequelize`).

3. **Import and use in your code:**

   **For pg (node-postgres):**
   ```javascript
   import pg from "pg";
   import { getEntraTokenPassword } from './entra-connection.js';
   
   const { Pool } = pg;
   
   const pool = new Pool({
     host: 'your-server.postgres.database.azure.com',
     port: 5432,
     database: 'your-database',
     user: 'your-user@yourdomain.onmicrosoft.com',
     password: getEntraTokenPassword,  // Function callback
     ssl: { rejectUnauthorized: false }
   });
   ```

   **For Sequelize:**
   ```javascript
   import { Sequelize } from 'sequelize';
   import { configureEntraIdAuth } from './entra-connection.js';
   
   const sequelize = new Sequelize({
     dialect: 'postgres',
     host: 'your-server.postgres.database.azure.com',
     port: 5432,
     database: 'your-database',
     dialectOptions: {
       ssl: { rejectUnauthorized: false }
     }
   });
   
   // Enable automatic token refresh
   configureEntraIdAuth(sequelize);
   ```

4. **Configure authentication:**
   
   Ensure your application has access to Azure credentials through one of these methods:
   - Azure CLI: Run `az login` before running your app
   - Environment variables: Set `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`
   - Managed Identity: When running on Azure (App Service, VM, etc.)
   - VS Code: Sign in to Azure extension

The `entra-connection.js` module handles token acquisition, caching, and username extraction from JWT claims. You don't need to modify it—just import and use the functions as shown above.

### How Token Refresh Works (JavaScript)

The `entra-connection.js` module provides helper functions for Entra ID authentication:

1. **`getEntraTokenPassword()`**: Acquires an access token using `DefaultAzureCredential` from `@azure/identity`. This token is scoped for Azure Database for PostgreSQL (`https://ossrdbms-aad.database.windows.net/.default`).

2. **`configureEntraIdAuth(sequelizeInstance)`**: Configures Sequelize to automatically fetch fresh tokens before each connection using the `beforeConnect` hook. This ensures:
   - A fresh token is acquired for every new database connection
   - The token is injected as the password
   - The username is derived from token claims (upn, appid) if needed

3. **Token Lifecycle**:
   - **pg example**: Pass `getEntraTokenPassword` as a callback to the `password` field. The `pg` library will call this function dynamically each time a new connection is established, ensuring fresh tokens are always used.
   - **Sequelize example**: Token is refreshed automatically before each connection via the `beforeConnect` hook.

4. **Credential Discovery**: `DefaultAzureCredential` attempts authentication in this order:
   - Environment variables
   - Managed Identity
   - Azure CLI credentials
   - IntelliJ credentials
   - VS Code credentials
   - And more...

This design ensures tokens are always valid without manual refresh logic, and connection pools automatically handle token lifecycle.

## Dotnet Usage

### Prerequisites
- .NET 8.0 or 9.0 SDK installed
  - Optional: .NET 10.0 SDK if you want to build/run for `net10.0`
- Npgsql (for PostgreSQL integration, if needed)

### Example Usage
1. Copy `appsettings.example.json` to `appsettings.json` and fill in your credentials:
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

### Using in Your Own Project

To integrate Entra ID authentication into your own .NET project, follow these steps:

1. **Copy the helper module:**
   
   Copy `dotnet/NpgsqlDataSourceBuilderExtensions.cs` from this repository into your project.

2. **Install required dependencies:**
   
   ```bash
   dotnet add package Npgsql
   dotnet add package Azure.Identity
   ```

3. **Import and use in your code:**

   **Synchronous approach:**
   ```csharp
   using Npgsql;
   using Azure.Identity;
   
   var connectionString = "Host=your-server.postgres.database.azure.com;Port=5432;Database=your-database;SSL Mode=Require";
   
   var dataSourceBuilder = new NpgsqlDataSourceBuilder(connectionString);
   
   // Enable Entra ID authentication
   dataSourceBuilder.UseEntraAuthentication();
   
   await using var dataSource = dataSourceBuilder.Build();
   await using var connection = await dataSource.OpenConnectionAsync();
   
   // Use the connection
   await using var cmd = new NpgsqlCommand("SELECT current_user", connection);
   var user = await cmd.ExecuteScalarAsync();
   Console.WriteLine($"Connected as: {user}");
   ```

   **Asynchronous approach:**
   ```csharp
   using Npgsql;
   using Azure.Identity;
   
   var connectionString = "Host=your-server.postgres.database.azure.com;Port=5432;Database=your-database;SSL Mode=Require";
   
   var dataSourceBuilder = new NpgsqlDataSourceBuilder(connectionString);
   
   // Enable Entra ID authentication with async token acquisition
   await dataSourceBuilder.UseEntraAuthenticationAsync();
   
   await using var dataSource = dataSourceBuilder.Build();
   await using var connection = await dataSource.OpenConnectionAsync();
   
   // Use the connection
   await using var cmd = new NpgsqlCommand("SELECT current_user", connection);
   var user = await cmd.ExecuteScalarAsync();
   Console.WriteLine($"Connected as: {user}");
   ```

4. **Configure authentication:**
   
   Ensure your application has access to Azure credentials through one of these methods:
   - **Azure CLI**: Run `az login` before running your app (local development)
   - **Environment variables**: Set `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`
   - **Managed Identity**: When running on Azure (App Service, Container Apps, VM, AKS, etc.)
   - **Visual Studio / VS Code**: Sign in to Azure
   - **Other**: Any method supported by `DefaultAzureCredential`

The `NpgsqlDataSourceBuilderExtensions` class handles token acquisition, automatic refresh, and username extraction from JWT claims. You don't need to modify it—just use the extension methods as shown above.

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
