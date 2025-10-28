# Copyright (c) Microsoft. All rights reserved.

class AzurePgEntraError(Exception):
    """Base class for all custom exceptions in the project."""

    pass


class TokenDecodeError(AzurePgEntraError):
    """Raised when a token value is invalid."""

    pass


class UsernameExtractionError(AzurePgEntraError):
    """Raised when username cannot be extracted from token."""

    pass


class CredentialValueError(AzurePgEntraError):
    """Raised when token credential is invalid."""

    pass


class EntraConnectionValueError(AzurePgEntraError):
    """Raised when Entra connection credentials are invalid."""

    pass


class ScopePermissionError(AzurePgEntraError):
    """Raised when the provided scope does not have sufficient permissions."""

    pass
