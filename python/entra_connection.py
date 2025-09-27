# Copyright (c) Microsoft. All rights reserved.
"""
Asynchronous connection class for using Entra auth with Azure DB for PostgreSQL.
This module provides an `AsyncEntraConnection` class that allows you to connect to Azure DB for PostgreSQL
using Entra authentication with psycopg. It handles token acquisition and connection setup. It is not specific
to this repository and can be used in any project that requires Entra authentication with Azure DB for PostgreSQL.

For example:
    
    from psycopg_pool import AsyncConnectionPool

    async with AsyncConnectionPool("<connection string>", connection_class=AsyncEntraConnection) as pool:
        ...

"""

import base64
import json
import logging
from functools import lru_cache

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity import DefaultAzureCredential
from psycopg import AsyncConnection

AZURE_DB_FOR_POSTGRES_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"
AZURE_MANAGEMENT_SCOPE = "https://management.azure.com/.default"

logger = logging.getLogger(__name__)


async def get_entra_token_async(credential: AsyncTokenCredential, scope: str) -> str:
    """Asynchronously acquires an Entra authentication token for Azure PostgreSQL.

    Parameters:
        credential (AsyncTokenCredential): Asynchronous credential used to obtain the token.

    Returns:
        str: The acquired authentication token to be used as the database password.
    """
    logger.info("Acquiring Entra token for postgres password")

    async with credential:
        cred = await credential.get_token(scope)
        return cred.token


def get_entra_token(credential: TokenCredential | None, scope: str) -> str:
    """Acquires an Entra authentication token for Azure PostgreSQL synchronously.

    Parameters:
        credential (TokenCredential or None): Credential object used to obtain the token. 
            If None, the default Azure credentials are used.

    Returns:
        str: The token string representing the authentication token.
    """
    logger.info("Acquiring Entra token for postgres password")
    credential = credential or get_default_azure_credentials()

    return credential.get_token(scope).token


@lru_cache(maxsize=1)
def get_default_azure_credentials() -> DefaultAzureCredential:
    """Retrieves and caches the default Azure credentials.

    Returns:
        DefaultAzureCredential: A singleton instance of the default Azure credentials.
    """
    return DefaultAzureCredential()


def decode_jwt(token):
    """Decodes a JWT token to extract its payload claims.

    Parameters:
        token (str): The JWT token string in the standard three-part format.

    Returns:
        dict: A dictionary containing the claims extracted from the token payload.
    """
    payload = token.split(".")[1]
    padding = "=" * (4 - len(payload) % 4)
    decoded_payload = base64.urlsafe_b64decode(payload + padding)
    return json.loads(decoded_payload)

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
    last_slash_index = xms_mirid.rfind('/')
    if last_slash_index == -1:
        return None

    beginning = xms_mirid[:last_slash_index]
    principal_name = xms_mirid[last_slash_index + 1:]

    if not principal_name or not beginning.lower().endswith("providers/microsoft.managedidentity/userassignedidentities"):
        return None

    return principal_name


async def get_entra_conninfo(credential: TokenCredential | AsyncTokenCredential | None) -> dict[str, str]:
    """Obtains connection information from Entra authentication for Azure PostgreSQL.

    Parameters:
        credential (TokenCredential, AsyncTokenCredential, or None): The credential used for token acquisition.
            If None, the default Azure credentials are used.

    Returns:
        dict[str, str]: A dictionary with 'user' and 'password' keys containing the username and token.
    
    Raises:
        ValueError: If the username cannot be extracted from the token payload.
    """
    # Fetch a new token and extract the username
    if isinstance(credential, AsyncTokenCredential):
        token = await get_entra_token_async(credential, AZURE_DB_FOR_POSTGRES_SCOPE)
    else:
        token = get_entra_token(credential, AZURE_DB_FOR_POSTGRES_SCOPE)
    claims = decode_jwt(token)
    username = (
        parse_principal_name(claims.get("xms_mirid"))
        or claims.get("upn")
        or claims.get("preferred_username")
        or claims.get("unique_name")
    )
    if not username:
        # Fall back to management scope ONLY to discover username
        if isinstance(credential, AsyncTokenCredential):
            token = await get_entra_token_async(credential, AZURE_MANAGEMENT_SCOPE)
        else:
            token = get_entra_token(credential, AZURE_MANAGEMENT_SCOPE)
        claims = decode_jwt(token)
        username = (
            parse_principal_name(claims.get("xms_mirid"))
            or claims.get("upn")
            or claims.get("preferred_username")
            or claims.get("unique_name")
        )

    if not username:
        raise ValueError(
            "Could not determine username from token claims. "
            "Ensure the identity has the proper Azure Entra ID attributes."
        )

    return {"user": username, "password": token}


class AsyncEntraConnection(AsyncConnection):
    """Asynchronous connection class for using Entra authentication with Azure PostgreSQL."""
    
    @classmethod
    async def connect(cls, *args, **kwargs):
        """Establishes an asynchronous PostgreSQL connection using Entra authentication.

        The method checks for provided credentials. If the 'user' or 'password' are not set
        in the keyword arguments, it acquires them from Entra via the provided or default credential.

        Parameters:
            *args: Positional arguments to be forwarded to the parent connection method.
            **kwargs: Keyword arguments including optional 'credential', and optionally 'user' and 'password'.

        Returns:
            AsyncConnection: An open asynchronous connection to the PostgreSQL database.

        Raises:
            ValueError: If the provided credential is not a valid TokenCredential or AsyncTokenCredential.
        """
        credential = kwargs.pop("credential", None)
        if credential and not isinstance(credential, (TokenCredential, AsyncTokenCredential)):
            raise ValueError("credential must be a TokenCredential or AsyncTokenCredential")
        if not kwargs.get("user") or not kwargs.get("password"):
            credential = credential or get_default_azure_credentials()
            entra_conninfo = await get_entra_conninfo(credential)
            kwargs["password"] = entra_conninfo["password"]
            if not kwargs.get("user"):
                # If user isn't already set, use the username from the token
                kwargs["user"] = entra_conninfo["user"]
        return await super().connect(*args, **kwargs | entra_conninfo)