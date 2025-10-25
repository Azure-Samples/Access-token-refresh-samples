using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Npgsql;
using Postgres.EntraAuth;

/// <summary>
/// This example enables Entra authentication before connecting to the database via NpgsqlConnection.
/// </summary>
public class Sample
{
    private static IConfiguration _configuration = null!;

    static async Task Main(string[] args)
    {
        // Build configuration from appsettings.json and environment variables
        _configuration = new ConfigurationBuilder()
            .SetBasePath(Directory.GetCurrentDirectory())
            .AddJsonFile("appsettings.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .Build();
        var connectionString = BuildConnectionString();

        Console.WriteLine("Testing Entra Authentication Methods");
        Console.WriteLine("=====================================");

        // Test synchronous method
        Console.WriteLine("\n1. Testing UseEntraAuthentication (Synchronous):");
        await ExecuteQueriesWithEntraAuth(connectionString, useAsync: false);

        // Test asynchronous method
        Console.WriteLine("\n2. Testing UseEntraAuthenticationAsync (Asynchronous):");
        await ExecuteQueriesWithEntraAuth(connectionString, useAsync: true);

        Console.WriteLine("\nAll tests completed.");
    }

    /// <summary>
    /// Show how to create a connection to the database with Entra authentication and execute some prompts.
    /// </summary>
    /// <param name="connectionString">The PostgreSQL connection string</param>
    /// <param name="useAsync">If true, uses UseEntraAuthenticationAsync; otherwise uses UseEntraAuthentication</param>
    private static async Task ExecuteQueriesWithEntraAuth(string connectionString, bool useAsync = false)
    {

        var dataSourceBuilder = new NpgsqlDataSourceBuilder(connectionString);

        // Here, we use the appropriate extension method provided by NpgsqlDataSourceBuilderExtensions.cs
        // to enable Entra Authentication. This will handle token acquisition, username extraction, and
        // token refresh as needed. If you copy NpgsqlDataSourceBuilderExtensions.cs into your project and
        // add the proper using statement, you should be able to directly call this method on a NpgsqlDataSourceBuilder
        // to enable Entra authentication in your application.
        if (useAsync)
        {
            await dataSourceBuilder.UseEntraAuthenticationAsync();
        }
        else
        {
            dataSourceBuilder.UseEntraAuthentication();
        }

        using var dataSource = dataSourceBuilder.Build();
        await using var connection = await dataSource.OpenConnectionAsync();

        // Get PostgreSQL version
        using var cmd1 = new NpgsqlCommand("SELECT version()", connection);
        var version = await cmd1.ExecuteScalarAsync();
        Console.WriteLine($"PostgreSQL Version: {version}");
    }

    private static string BuildConnectionString()
    {
        // Read configuration values from appsettings.json or environment variables
        var server = _configuration["Host"];
        var database = _configuration["Database"] ?? "postgres";
        var port = _configuration.GetValue<int>("Port", 5432);
        var sslMode = _configuration["SslMode"] ?? "Require";
        if (string.IsNullOrEmpty(server))
        {
            throw new InvalidOperationException("Host must be configured in appsettings.json or as environment variable 'Host'");
        }

        return $"Host={server};Database={database};Port={port};SSL Mode={sslMode};";
    }
}
