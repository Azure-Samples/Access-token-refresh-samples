# Copyright (c) Microsoft. All rights reserved.

import base64
import json
from typing import Any, cast

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import CredentialUnavailableError
from azure.identity import DefaultAzureCredential as DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential

from errors import (
    ScopePermissionError,
    TokenDecodeError,
    UsernameExtractionError,
)

AZURE_DB_FOR_POSTGRES_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"
AZURE_MANAGEMENT_SCOPE = "https://management.azure.com/.default"


def get_entra_token(credential: TokenCredential | None, scope: str) -> str:
    """Acquires an Entra authentication token for Azure PostgreSQL synchronously.

    Parameters:
        credential (TokenCredential or None): Credential object used to obtain the token.
            If None, the default Azure credentials are used.
        scope (str): The scope for the token request.

    Returns:
        str: The acquired authentication token to be used as the database password.
    """
    credential = credential or DefaultAzureCredential()
    cred = credential.get_token(scope)
    return cred.token


async def get_entra_token_async(
    credential: AsyncTokenCredential | None, scope: str
) -> str:
    """Asynchronously acquires an Entra authentication token for Azure PostgreSQL.

    Parameters:
        credential (AsyncTokenCredential or None): Asynchronous credential used to obtain the token.
            If None, the default Azure credentials are used.
        scope (str): The scope for the token request.

    Returns:
        str: The acquired authentication token to be used as the database password.
    """
    credential = credential or AsyncDefaultAzureCredential()
    async with credential:
        cred = await credential.get_token(scope)
        return cred.token


def decode_jwt(token: str) -> dict[str, Any]:
    """Decodes a JWT token to extract its payload claims.

    Parameters:
        token (str): The JWT token string in the standard three-part format.

    Returns:
        dict[str, Any]: A dictionary containing the claims extracted from the token payload.

    Raises:
        TokenValueError: If the token format is invalid or cannot be decoded.
    """
    try:
        payload = token.split(".")[1]
        padding = "=" * (4 - len(payload) % 4)
        decoded_payload = base64.urlsafe_b64decode(payload + padding)
        return cast(dict[str, Any], json.loads(decoded_payload))
    except Exception as e:
        raise TokenDecodeError("Invalid JWT token format") from e


def parse_principal_name(xms_mirid: str) -> str | None:
    """Parses the principal name from an Azure resource path.

    Parameters:
        xms_mirid (str): The xms_mirid claim value containing the Azure resource path.

    Returns:
        str | None: The extracted principal name, or None if parsing fails.
    """
    if not xms_mirid:
        return None

    # Parse the xms_mirid claim which looks like
    # /subscriptions/{subId}/resourcegroups/{resourceGroup}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{principalName}
    last_slash_index = xms_mirid.rfind("/")
    if last_slash_index == -1:
        return None

    beginning = xms_mirid[:last_slash_index]
    principal_name = xms_mirid[last_slash_index + 1 :]

    if not principal_name or not beginning.lower().endswith(
        "providers/microsoft.managedidentity/userassignedidentities"
    ):
        return None

    return principal_name


def get_entra_conninfo(credential: TokenCredential | None) -> dict[str, str]:
    """Synchronously obtains connection information from Entra authentication for Azure PostgreSQL.

    This function acquires an access token from Azure Entra ID and extracts the username
    from the token claims. It tries multiple claim sources to determine the username.

    Parameters:
        credential (TokenCredential or None): The credential used for token acquisition.
            If None, DefaultAzureCredential() is used to automatically discover credentials.

    Returns:
        dict[str, str]: A dictionary with 'user' and 'password' keys, where:
            - 'user': The extracted username from token claims
            - 'password': The Entra ID access token for database authentication

    Raises:
        TokenDecodeError: If the JWT token cannot be decoded or is malformed.
        UsernameExtractionError: If the username cannot be extracted from token claims.
        ScopePermissionError: The token could not be acquired from the management scope, possibly due to insufficient permissions.
    """
    credential = credential or DefaultAzureCredential()

    # Always get the DB-scope token for password
    db_token = get_entra_token(credential, AZURE_DB_FOR_POSTGRES_SCOPE)
    try:
        db_claims = decode_jwt(db_token)
    except TokenDecodeError:
        raise
    xms_mirid = db_claims.get("xms_mirid")
    username = (
        parse_principal_name(xms_mirid)
        if isinstance(xms_mirid, str)
        else None
        or db_claims.get("upn")
        or db_claims.get("preferred_username")
        or db_claims.get("unique_name")
    )

    if not username:
        # Fall back to management scope ONLY to discover username
        try:
            mgmt_token = get_entra_token(credential, AZURE_MANAGEMENT_SCOPE)
        except (CredentialUnavailableError, ClientAuthenticationError) as e:
            raise ScopePermissionError(
                "Failed to acquire token from management scope"
            ) from e
        try:
            mgmt_claims = decode_jwt(mgmt_token)
        except TokenDecodeError:
            raise
        xms_mirid = mgmt_claims.get("xms_mirid")
        username = (
            parse_principal_name(xms_mirid)
            if isinstance(xms_mirid, str)
            else None
            or mgmt_claims.get("upn")
            or mgmt_claims.get("preferred_username")
            or mgmt_claims.get("unique_name")
        )

    if not username:
        raise UsernameExtractionError(
            "Could not determine username from token claims. "
            "Ensure the identity has the proper Azure AD attributes."
        )

    return {"user": username, "password": db_token}


async def get_entra_conninfo_async(
    credential: AsyncTokenCredential | None,
) -> dict[str, str]:
    """Asynchronously obtains connection information from Entra authentication for Azure PostgreSQL.

    This function acquires an access token from Azure Entra ID and extracts the username
    from the token claims. It tries multiple claim sources to determine the username.

    Parameters:
        credential (AsyncTokenCredential or None): The async credential used for token acquisition.
            If None, AsyncDefaultAzureCredential() is used to automatically discover credentials.

    Returns:
        dict[str, str]: A dictionary with 'user' and 'password' keys, where:
            - 'user': The extracted username from token claims
            - 'password': The Entra ID access token for database authentication

    Raises:
        TokenDecodeError: If the JWT token cannot be decoded or is malformed.
        UsernameExtractionError: If the username cannot be extracted from token claims.
        ScopePermissionError: The token could not be acquired from the management scope, possibly due to insufficient permissions.
    """
    credential = credential or AsyncDefaultAzureCredential()

    db_token = await get_entra_token_async(credential, AZURE_DB_FOR_POSTGRES_SCOPE)
    try:
        db_claims = decode_jwt(db_token)
    except TokenDecodeError:
        raise
    xms_mirid = db_claims.get("xms_mirid")
    username = (
        parse_principal_name(xms_mirid)
        if isinstance(xms_mirid, str)
        else None
        or db_claims.get("upn")
        or db_claims.get("preferred_username")
        or db_claims.get("unique_name")
    )

    if not username:
        try:
            mgmt_token = await get_entra_token_async(credential, AZURE_MANAGEMENT_SCOPE)
        except (CredentialUnavailableError, ClientAuthenticationError) as e:
            raise ScopePermissionError(
                "Failed to acquire token from management scope"
            ) from e
        try:
            mgmt_claims = decode_jwt(mgmt_token)
        except TokenDecodeError:
            raise
        xms_mirid = mgmt_claims.get("xms_mirid")
        username = (
            parse_principal_name(xms_mirid)
            if isinstance(xms_mirid, str)
            else None
            or mgmt_claims.get("upn")
            or mgmt_claims.get("preferred_username")
            or mgmt_claims.get("unique_name")
        )

    if not username:
        raise UsernameExtractionError(
            "Could not determine username from token claims. "
            "Ensure the identity has the proper Azure AD attributes."
        )

    return {"user": username, "password": db_token}
