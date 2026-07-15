"""Buckaroo SDK for Python.

Public API:

    from buckaroo import Buckaroo, BuckarooClient
    from buckaroo import BuckarooError, AuthenticationError, ParameterValidationError, BuckarooApiError
"""

from buckaroo._version import VERSION
from buckaroo.app import Buckaroo
from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.exceptions._buckaroo_error import BuckarooError
from buckaroo.exceptions._authentication_error import AuthenticationError
from buckaroo.exceptions._parameter_validation_error import ParameterValidationError
from buckaroo.http.client import BuckarooApiError

__version__ = VERSION

__all__ = [
    "__version__",
    "Buckaroo",
    "BuckarooClient",
    "BuckarooError",
    "AuthenticationError",
    "ParameterValidationError",
    "BuckarooApiError",
]
