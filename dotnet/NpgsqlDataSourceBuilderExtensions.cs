// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using Azure.Core;
using Azure.Identity;
using Npgsql;

namespace Postgres.EntraAuth;

/// <summary>
/// Extension methods for NpgsqlDataSourceBuilder to enable Entra authentication with Azure DB for PostgreSQL.
/// This class provides methods to configure NpgsqlDataSourceBuilder to use Entra authentication, handling token
/// acquisition and connection setup. It is not specific to this repository and can be used in any project that
/// requires Entra authentication with Azure DB for PostgreSQL.
/// 
/// Example usage:
/// <code>
/// using Npgsql;
/// using Postgres.EntraAuth;
/// 
/// var dataSourceBuilder = new NpgsqlDataSourceBuilder("<connection string>");
/// dataSourceBuilder.UseEntraAuthentication();
/// var dataSource = dataSourceBuilder.Build();
/// </code>
/// </summary>
public static class NpgsqlDataSourceBuilderExtensions
{
    private static readonly TokenRequestContext s_azureDBForPostgresTokenRequestContext = new([Constants.AzureDBForPostgresScope]);
    private static readonly TokenRequestContext s_managementTokenRequestContext = new([Constants.AzureManagementScope]);

 /// <summary>
    /// Configures the NpgsqlDataSourceBuilder to use Entra ID authentication synchronously.
    /// </summary>
    /// <param name="dataSourceBuilder">The NpgsqlDataSourceBuilder to configure.</param>
    /// <param name="credential">The TokenCredential to use for authentication. If null, DefaultAzureCredential is used.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
    /// <returns>The configured NpgsqlDataSourceBuilder.</returns>
    public static NpgsqlDataSourceBuilder UseEntraAuthentication(this NpgsqlDataSourceBuilder dataSourceBuilder, TokenCredential? credential = default, CancellationToken cancellationToken = default)
    {
        credential ??= new DefaultAzureCredential();

        if (dataSourceBuilder.ConnectionStringBuilder.Username == null)
        {

            // Ensure to use the management scope, so the token contains user names for all managed identity types - e.g. user and service principal
            var token = credential.GetToken(s_managementTokenRequestContext, cancellationToken);
            var username = TryGetUsernameFromToken(token.Token);

            if (username != null)
            {
                dataSourceBuilder.ConnectionStringBuilder.Username = username;
            }
            else
            {
                // Otherwise check using the PostgresSql scope
                token = credential.GetToken(s_azureDBForPostgresTokenRequestContext, cancellationToken);
                SetUsernameFromToken(dataSourceBuilder, token.Token);
            }
        }

        SetPasswordProvider(dataSourceBuilder, credential, s_azureDBForPostgresTokenRequestContext);

        return dataSourceBuilder;
    }

    /// <summary>
    /// Configures the NpgsqlDataSourceBuilder to use Entra ID authentication asynchronously.
    /// </summary>
    /// <param name="dataSourceBuilder">The NpgsqlDataSourceBuilder to configure.</param>
    /// <param name="credential">The TokenCredential to use for authentication. If null, DefaultAzureCredential is used.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the configured NpgsqlDataSourceBuilder.</returns>
    public static async Task<NpgsqlDataSourceBuilder> UseEntraAuthenticationAsync(this NpgsqlDataSourceBuilder dataSourceBuilder, TokenCredential? credential = default, CancellationToken cancellationToken = default)
    {
        credential ??= new DefaultAzureCredential();

        if (dataSourceBuilder.ConnectionStringBuilder.Username == null)
        {

            // Ensure to use the management scope, so the token contains user names for all managed identity types - e.g. user and service principal
            var token = await credential.GetTokenAsync(s_managementTokenRequestContext, cancellationToken).ConfigureAwait(false);
            var username = TryGetUsernameFromToken(token.Token);

            if (username != null)
            {
                dataSourceBuilder.ConnectionStringBuilder.Username = username;
            }
            else
            {
                // Otherwise check using the PostgresSql scope
                token = await credential.GetTokenAsync(s_azureDBForPostgresTokenRequestContext, cancellationToken).ConfigureAwait(false);
                SetUsernameFromToken(dataSourceBuilder, token.Token);
            }
        }

        SetPasswordProvider(dataSourceBuilder, credential, s_azureDBForPostgresTokenRequestContext);

        return dataSourceBuilder;
    }

    private static void SetPasswordProvider(NpgsqlDataSourceBuilder dataSourceBuilder, TokenCredential credential, TokenRequestContext tokenRequestContext)
    {
        dataSourceBuilder.UsePasswordProvider(_ =>
        {
            var token = credential.GetToken(tokenRequestContext, default);
            return token.Token;
        }, async (_, ct) =>
        {
            // Use the cancellation token provided by Npgsql for async operations
            var token = await credential.GetTokenAsync(tokenRequestContext, ct).ConfigureAwait(false);
            return token.Token;
        });
    }

    private static void SetUsernameFromToken(NpgsqlDataSourceBuilder dataSourceBuilder, string token)
    {
        var username = TryGetUsernameFromToken(token);

        if (username != null)
        {
            dataSourceBuilder.ConnectionStringBuilder.Username = username;
        }
        else
        {
            throw new Exception("Could not determine username from token claims");
        }
    }

    private static string? TryGetUsernameFromToken(string jwtToken)
    {
        // Split the token into its parts (Header, Payload, Signature)
        var tokenParts = jwtToken.Split('.');
        if (tokenParts.Length != 3)
        {
            return null;
        }

        // The payload is the second part, Base64Url encoded
        var payload = tokenParts[1];
        if (string.IsNullOrWhiteSpace(payload))
        {
            return null; // empty payload
        }

        try
        {
            // Add padding if necessary
            payload = AddBase64Padding(payload);

            // Convert from Base64Url to standard Base64
            payload = payload.Replace('-', '+').Replace('_', '/');

            // Decode the payload from Base64
            var decodedBytes = Convert.FromBase64String(payload);
            var decodedPayload = Encoding.UTF8.GetString(decodedBytes);

            if (string.IsNullOrWhiteSpace(decodedPayload))
            {
                return null; // nothing to parse
            }

            // Parse the decoded payload as JSON
            var payloadJson = JsonSerializer.Deserialize<JsonElement>(decodedPayload);

            // Try to get the username from 'xms_mirid', 'upn', 'preferred_username', or 'unique_name' claims
            if (payloadJson.TryGetProperty("xms_mirid", out var xms_mirid) &&
                xms_mirid.GetString() is string xms_miridString &&
                ParsePrincipalName(xms_miridString) is string principalName)
            {
                return principalName;
            }
            else if (payloadJson.TryGetProperty("upn", out var upn))
            {
                return upn.GetString();
            }
            else if (payloadJson.TryGetProperty("preferred_username", out var preferredUsername))
            {
                return preferredUsername.GetString();
            }
            else if (payloadJson.TryGetProperty("unique_name", out var uniqueName))
            {
                return uniqueName.GetString();
            }

            return null; // no relevant claims
        }
        catch (FormatException)
        {
            // Invalid Base64 content
            return null;
        }
        catch (JsonException)
        {
            // Invalid JSON content
            return null;
        }
    }

    private static string? ParsePrincipalName(string xms_mirid)
    {
        // parse the xms_mirid claim which looks like
        // /subscriptions/{subId}/resourcegroups/{resourceGroup}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{principalName}
        var lastSlashIndex = xms_mirid.LastIndexOf('/');
        if (lastSlashIndex == -1)
        {
            return null;
        }

        var beginning = xms_mirid.AsSpan(0, lastSlashIndex);
        var principalName = xms_mirid.AsSpan(lastSlashIndex + 1);

        if (principalName.IsEmpty || !beginning.EndsWith("providers/Microsoft.ManagedIdentity/userAssignedIdentities", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        return principalName.ToString();
    }

    private static string AddBase64Padding(string base64) => (base64.Length % 4) switch
    {
        2 => base64 + "==",
        3 => base64 + "=",
        _ => base64,
    };
}
