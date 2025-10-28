# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from azure.core.credentials import TokenCredential

try:
    from psycopg import Connection
except ImportError as e:
    raise ImportError(
        "psycopg3 dependencies are not installed. "
        "Install them with: pip install azurepg-entra[psycopg3]"
    ) from e

from shared import get_entra_conninfo
from errors import (
    CredentialValueError,
    EntraConnectionValueError,
)


class EntraConnection(Connection):
    """Synchronous connection class for using Entra authentication with Azure PostgreSQL."""

    @classmethod
    def connect(cls, *args: Any, **kwargs: Any) -> "EntraConnection":
        """Establishes a synchronous PostgreSQL connection using Entra authentication.

        This method automatically acquires Azure Entra ID credentials when user or password
        are not provided in the connection parameters. If authentication fails, the original
        exception is re-raised to the caller.

        Parameters:
            *args: Positional arguments to be forwarded to the parent connection method.
            **kwargs: Keyword arguments including:
                - credential (TokenCredential, optional): Azure credential for token acquisition.
                - user (str, optional): Database username. If not provided, extracted from Entra token.
                - password (str, optional): Database password. If not provided, uses Entra access token.

        Returns:
            EntraConnection: An open synchronous connection to the PostgreSQL database.

        Raises:
            CredentialValueError: If the provided credential is not a valid TokenCredential.
            EntraConnectionValueError: If Entra connection credentials cannot be retrieved
        """
        credential = kwargs.pop("credential", None)
        if credential and not isinstance(credential, (TokenCredential)):
            raise CredentialValueError(
                "credential must be a TokenCredential for sync connections"
            )

        # Check if we need to acquire Entra authentication info
        if not kwargs.get("user") or not kwargs.get("password"):
            try:
                entra_conninfo = get_entra_conninfo(credential)
            except Exception as e:
                raise EntraConnectionValueError(
                    "Could not retrieve Entra credentials"
                ) from e
            # Always use the token password when Entra authentication is needed
            kwargs["password"] = entra_conninfo["password"]
            if not kwargs.get("user"):
                # If user isn't already set, use the username from the token
                kwargs["user"] = entra_conninfo["user"]
        return super().connect(*args, **kwargs)
