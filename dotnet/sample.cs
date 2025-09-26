using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Npgsql;
using Postgres.EntraAuth;

class Sample
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

        Console.WriteLine("Testing Entra Authentication Methods");
        Console.WriteLine("=====================================");

        // Test synchronous method
        Console.WriteLine("\n1. Testing UseEntraAuthentication (Synchronous):");
        TestSyncEntraAuthentication();

        // Test asynchronous method
        Console.WriteLine("\n2. Testing UseEntraAuthenticationAsync (Asynchronous):");
        await TestAsyncEntraAuthentication();

        Console.WriteLine("\nAll tests completed.");
    }

    private static void TestSyncEntraAuthentication()
    {
        try
        {
            var connectionString = BuildConnectionString();
            var credential = new DefaultAzureCredential();
            var dataSourceBuilder = new NpgsqlDataSourceBuilder(connectionString);            
            // This line uses the extension method provided by dotnet/NpgsqlDataSourceBuilderExtensions.cs
            // to enable Entra Authentication. If you copy dotnet/NpgsqlDataSourceBuilderExtensions.cs into your
            // project and add the proper using statement, you should be able to directly call this on a
            // NpgsqlDataSourceBuilder to enable Entra authentication in your application.
            dataSourceBuilder.UseEntraAuthentication(credential);
            using var dataSource = dataSourceBuilder.Build();
            using var conn = dataSource.OpenConnection();    
            Console.WriteLine("✓ Successfully connected using synchronous authentication.");    
            using var cmd = new NpgsqlCommand("SELECT NOW() as current_time, 'sync' as method", conn);
            var result = cmd.ExecuteScalar();
            Console.WriteLine($"✓ Query result: {result}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"✗ Synchronous test failed: {ex.Message}");
        }
    }

    private static async Task TestAsyncEntraAuthentication()
    {
        try
        {
            var connectionString = BuildConnectionString();
            var credential = new DefaultAzureCredential();
            var dataSourceBuilder = new NpgsqlDataSourceBuilder(connectionString);
            // This line uses the extension method provided by dotnet/NpgsqlDataSourceBuilderExtensions.cs
            // to enable Entra Authentication. If you copy dotnet/NpgsqlDataSourceBuilderExtensions.cs into your
            // project and add the proper using statement, you should be able to directly call this on a
            // NpgsqlDataSourceBuilder to enable Entra authentication in your application
            await dataSourceBuilder.UseEntraAuthenticationAsync(credential);
            using var dataSource = dataSourceBuilder.Build();
            using var conn = await dataSource.OpenConnectionAsync();
            Console.WriteLine("✓ Successfully connected using asynchronous authentication.");
            using var cmd = new NpgsqlCommand("SELECT NOW() as current_time, 'async' as method", conn);
            var result = await cmd.ExecuteScalarAsync();
            Console.WriteLine($"✓ Query result: {result}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"✗ Asynchronous test failed: {ex.Message}");
        }
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
