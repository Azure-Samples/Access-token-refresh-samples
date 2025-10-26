# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from azure.core.credentials_async import AsyncTokenCredential

try:
    from psycopg import AsyncConnection
except ImportError as e:
    raise ImportError(
        "psycopg3 dependencies are not installed. "
        "Install them with: pip install azurepg-entra[psycopg3]"
    ) from e

import sys
sys.path.append('../python')

from core import get_entra_conninfo_async
from errors import (
    CredentialValueError,
    EntraConnectionValueError,
)


class AsyncEntraConnection(AsyncConnection):
    """Asynchronous connection class for using Entra authentication with Azure PostgreSQL."""

    @classmethod
    async def connect(cls, *args: Any, **kwargs: Any) -> "AsyncEntraConnection":
        """Establishes an asynchronous PostgreSQL connection using Entra authentication.

        This method automatically acquires Azure Entra ID credentials when user or password
        are not provided in the connection parameters. Authentication errors are printed to
        console for debugging purposes.

        Parameters:
            *args: Positional arguments to be forwarded to the parent connection method.
            **kwargs: Keyword arguments including:
                - credential (AsyncTokenCredential, optional): Async Azure credential for token acquisition.
                - user (str, optional): Database username. If not provided, extracted from Entra token.
                - password (str, optional): Database password. If not provided, uses Entra access token.

        Returns:
            AsyncEntraConnection: An open asynchronous connection to the PostgreSQL database.

        Raises:
            CredentialValueError: If the provided credential is not a valid AsyncTokenCredential.
            EntraConnectionValueError: If Entra connection credentials are invalid.
        """
        credential = kwargs.pop("credential", None)
        if credential and not isinstance(credential, (AsyncTokenCredential)):
            raise CredentialValueError(
                "credential must be an AsyncTokenCredential for async connections"
            )

        # Check if we need to acquire Entra authentication info
        if not kwargs.get("user") or not kwargs.get("password"):
            try:
                entra_conninfo = await get_entra_conninfo_async(credential)
            except Exception as e:
                raise EntraConnectionValueError(
                    "Could not retrieve Entra credentials"
                ) from e
            # Always use the token password when Entra authentication is needed
            kwargs["password"] = entra_conninfo["password"]
            if not kwargs.get("user"):
                # If user isn't already set, use the username from the token
                kwargs["user"] = entra_conninfo["user"]
        return await super().connect(*args, **kwargs)
