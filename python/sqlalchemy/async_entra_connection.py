# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from azure.core.credentials import TokenCredential

try:
    from sqlalchemy import event
    from sqlalchemy.engine import Dialect
    from sqlalchemy.ext.asyncio import AsyncEngine
except ImportError as e:
    # Provide a helpful error message if SQLAlchemy dependencies are missing
    raise ImportError(
        "SQLAlchemy dependencies are not installed. "
        "Install them with: pip install azurepg-entra[sqlalchemy]"
    ) from e

import sys
from pathlib import Path

# Add parent directory (python folder) to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import get_entra_conninfo
from errors import (
    CredentialValueError,
    EntraConnectionValueError,
)


def enable_entra_authentication_async(engine: AsyncEngine) -> None:
    """
    Enable Azure Entra ID authentication for an async SQLAlchemy engine.

    This function registers an event listener that automatically provides
    Entra ID credentials for each database connection if they are not already set.
    Event handlers do not support async behavior so the token fetching will still
    be synchronous.

    Args:
        engine: The async SQLAlchemy Engine to enable Entra authentication for
    """

    @event.listens_for(engine.sync_engine, "do_connect")
    def provide_token(
        dialect: Dialect, conn_rec: Any, cargs: Any, cparams: dict[str, Any]
    ) -> None:
        """Event handler that provides Entra credentials for each sync connection.

        Raises:
            CredentialValueError: If the provided credential is not a valid TokenCredential.
            EntraConnectionValueError: If Entra connection credentials cannot be retrieved
        """
        credential = cparams.get("credential", None)
        if credential and not isinstance(credential, (TokenCredential)):
            raise CredentialValueError(
                "credential must be a TokenCredential for async connections"
            )
        # Check if credentials are already present
        has_user = "user" in cparams
        has_password = "password" in cparams

        # Only get Entra credentials if user or password is missing
        if not has_user or not has_password:
            try:
                entra_creds = get_entra_conninfo(credential)
            except Exception as e:
                raise EntraConnectionValueError(
                    "Could not retrieve Entra credentials"
                ) from e
            # Only update missing credentials
            if not has_user and "user" in entra_creds:
                cparams["user"] = entra_creds["user"]
            if not has_password and "password" in entra_creds:
                cparams["password"] = entra_creds["password"]
