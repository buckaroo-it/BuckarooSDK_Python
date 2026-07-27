"""Package skeleton: __init__.py, _version.py, py.typed (PEP 561)."""

import runpy
from pathlib import Path


def test_version_attribute_matches_version_module():
    import buckaroo
    from buckaroo import _version

    assert buckaroo.__version__ == _version.VERSION
    assert buckaroo.__version__ == "1.0.0"


def test_public_api_reexports():
    import buckaroo

    from buckaroo.app import Buckaroo as _Buckaroo
    from buckaroo._buckaroo_client import BuckarooClient as _BuckarooClient
    from buckaroo.exceptions._buckaroo_error import BuckarooError as _BuckarooError
    from buckaroo.exceptions._authentication_error import (
        AuthenticationError as _AuthenticationError,
    )
    from buckaroo.exceptions._parameter_validation_error import (
        ParameterValidationError as _ParameterValidationError,
    )

    assert buckaroo.Buckaroo is _Buckaroo
    assert buckaroo.BuckarooClient is _BuckarooClient
    assert buckaroo.BuckarooError is _BuckarooError
    assert buckaroo.AuthenticationError is _AuthenticationError
    assert buckaroo.ParameterValidationError is _ParameterValidationError


def test_py_typed_marker_exists_and_is_empty():
    import buckaroo

    pkg_dir = Path(buckaroo.__file__).parent
    marker = pkg_dir / "py.typed"

    assert marker.is_file(), "PEP 561 py.typed marker missing"
    assert marker.read_bytes() == b"", "py.typed must be empty per PEP 561"


def test_setup_py_can_read_version_module():
    """setup.py reads buckaroo/_version.py as a standalone script; runpy mirrors that."""
    import buckaroo

    version_file = Path(buckaroo.__file__).parent / "_version.py"
    namespace = runpy.run_path(str(version_file))

    assert namespace["VERSION"] == "1.0.0"
