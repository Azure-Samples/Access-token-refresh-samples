# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from azure.core.credentials import TokenCredential

import sys

sys.path.append('../python')

from core import get_entra_conninfo
from errors import (
    CredentialValueError,
    EntraConnectionValueError,
)

try:
    from psycopg2.extensions import connection, make_dsn, parse_dsn
except ImportError as e:
    # Provide a helpful error message if psycopg2 dependencies are missing
    raise ImportError(
        "psycopg2 dependencies are not installed. "
        "Install them with: pip install azurepg-entra[psycopg2]"
    ) from e

class EntraConnection(connection):
    """Establishes a synchronous PostgreSQL connection using Entra authentication.

    This connection class automatically acquires Azure Entra ID credentials when user
    or password are not provided in the DSN or connection parameters. Authentication
    errors are printed to console for debugging purposes.

    Parameters:
        dsn (str): PostgreSQL connection string (Data Source Name).
        **kwargs: Additional keyword arguments including:
            - credential (TokenCredential, optional): Azure credential for token acquisition.
              If None, DefaultAzureCredential() is used.
            - user (str, optional): Database username. If not provided, extracted from Entra token.
            - password (str, optional): Database password. If not provided, uses Entra access token.

    Raises:
        CredentialValueError: If the provided credential is not a valid TokenCredential.
        EntraConnectionValueError: If Entra connection credentials cannot be retrieved
    """

    def __init__(self, dsn: str, **kwargs: Any) -> None:
        # Extract current DSN params
        dsn_params = parse_dsn(dsn) if dsn else {}

        credential = kwargs.pop("credential", None)
        if credential and not isinstance(credential, (TokenCredential)):
            raise CredentialValueError(
                "credential must be a TokenCredential for sync connections"
            )

        # Check if user and password are already provided
        has_user = "user" in dsn_params or "user" in kwargs
        has_password = "password" in dsn_params or "password" in kwargs

        # Only get Entra credentials if user or password is missing
        if not has_user or not has_password:
            try:
                entra_creds = get_entra_conninfo(credential)
            except (Exception) as e:
                raise EntraConnectionValueError(
                    "Could not retrieve Entra credentials"
                ) from e

            # Only update missing credentials
            if not has_user and "user" in entra_creds:
                dsn_params["user"] = entra_creds["user"]
            if not has_password and "password" in entra_creds:
                dsn_params["password"] = entra_creds["password"]

        # Update DSN params with any kwargs (kwargs take precedence)
        dsn_params.update(kwargs)

        # Create new DSN with updated credentials
        new_dsn = make_dsn(**dsn_params)

        # Call parent constructor with updated DSN only
        super().__init__(new_dsn)
