"""Tests for :class:`buckaroo.services.service_parameter_validator.ServiceParameterValidator`.

Exercises the rules engine through real builders' rule tables loaded via
``get_allowed_service_parameters``. The parameterised tests intentionally
walk the registered builders so rule-table edits surface in assertions
automatically; explicit tests pin a few load-bearing edge cases.

The validator's conceptual public surface:

- ``validate(...)``  -> ``validate_all_parameters(..., strict=True)``
- ``filter(...)``    -> ``validate_and_filter_parameters(...)``
- ``get_allowed_parameters(...)`` -> ``get_parameter_info(...)``
"""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from buckaroo.builders.payments.credit_card_builder import CreditcardBuilder
from buckaroo.builders.payments.ideal_builder import IdealBuilder
from buckaroo.builders.payments.ideal_qr_builder import IdealQrBuilder
from buckaroo.builders.payments.klarna_builder import KlarnaBuilder
from buckaroo.builders.payments.sofort_builder import SofortBuilder
from buckaroo.exceptions._parameter_validation_error import (
    ParameterValidationError,
    RequiredParameterMissingError,
)
from buckaroo.models.payment_request import Parameter
from buckaroo.services.service_parameter_validator import ServiceParameterValidator


# ---------------------------------------------------------------------------
# Helpers


def _validator_for(builder_cls) -> ServiceParameterValidator:
    """Build a :class:`ServiceParameterValidator` around a real builder."""
    builder = builder_cls(MagicMock())
    return ServiceParameterValidator(builder)


def _stub_builder(allowed: Dict[str, Dict[str, Any]], service_name: str = "stub"):
    """Minimal fake builder exposing the two hooks the validator needs."""
    builder = MagicMock()
    builder.get_service_name.return_value = service_name
    builder.get_allowed_service_parameters.side_effect = lambda action="Pay": allowed.get(
        action, {}
    )
    return builder


# ---------------------------------------------------------------------------
# normalize_parameter_name — strips dots, underscores, and casing.


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("issuer", "issuer"),
        ("Issuer", "issuer"),
        ("service_parameters.issuer", "issuer"),
        ("encryptedcarddata", "encryptedcarddata"),
        ("Encrypted_Card_Data", "encryptedcarddata"),
    ],
)
def test_normalize_parameter_name_handles_case_underscores_and_dots(raw, expected):
    validator = _validator_for(IdealBuilder)
    assert validator.normalize_parameter_name(raw) == expected


# ---------------------------------------------------------------------------
# normalize_parameter_value — string booleans convert back to real booleans.


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("true", True),
        ("True", True),
        ("FALSE", False),
        ("false", False),
        ("hello", "hello"),
        ("", ""),
    ],
)
def test_normalize_parameter_value_maps_string_booleans(raw, expected):
    validator = _validator_for(IdealBuilder)
    assert validator.normalize_parameter_value(raw) == expected


# ---------------------------------------------------------------------------
# validate_parameter_type — no-ops and explicit type checks.


def test_validate_parameter_type_no_type_key_is_noop():
    validator = _validator_for(IdealBuilder)
    # No 'type' in config means no validation; should not raise.
    validator.validate_parameter_type("x", object(), {})


@pytest.mark.parametrize("structured", [list, dict])
def test_validate_parameter_type_skips_list_and_dict_expected_types(structured):
    validator = _validator_for(IdealBuilder)
    # Grouped params pass through without per-field type checks.
    validator.validate_parameter_type("x", "anything", {"type": structured})


def test_validate_parameter_type_string_mismatch_raises():
    validator = _validator_for(IdealBuilder)
    with pytest.raises(ParameterValidationError) as exc:
        validator.validate_parameter_type("issuer", 1234, {"type": str})
    assert "issuer" in str(exc.value)
    assert exc.value.parameter_name == "issuer"
    assert exc.value.service_name == "ideal"
    assert exc.value.expected_type == "str"


def test_validate_parameter_type_bool_string_true_passes():
    validator = _validator_for(IdealQrBuilder)
    # 'true'/'false' strings are accepted when expected type is bool.
    validator.validate_parameter_type("isOneOff", "true", {"type": bool})
    validator.validate_parameter_type("isOneOff", "FALSE", {"type": bool})


def test_validate_parameter_type_bool_non_boolean_string_raises():
    validator = _validator_for(IdealQrBuilder)
    with pytest.raises(ParameterValidationError) as exc:
        validator.validate_parameter_type("isOneOff", "maybe", {"type": bool})
    assert "boolean" in str(exc.value)
    assert exc.value.expected_type == "bool"


def test_validate_parameter_type_bool_non_string_non_bool_raises():
    validator = _validator_for(IdealQrBuilder)
    with pytest.raises(ParameterValidationError) as exc:
        validator.validate_parameter_type("isOneOff", 123, {"type": bool})
    assert "of type bool" in str(exc.value)


def test_validate_parameter_type_tuple_accepts_any_matching_type():
    validator = _validator_for(SofortBuilder)
    validator.validate_parameter_type("savetoken", True, {"type": (str, bool)})
    validator.validate_parameter_type("savetoken", "opaque", {"type": (str, bool)})


def test_validate_parameter_type_tuple_with_bool_accepts_true_false_string():
    validator = _validator_for(SofortBuilder)
    validator.validate_parameter_type("savetoken", "true", {"type": (str, bool)})


def test_validate_parameter_type_tuple_with_bool_rejects_non_boolean_string():
    # Tuple (int, bool) forbids arbitrary strings and only accepts
    # 'true'/'false' strings via the bool-in-tuple path.
    validator = _validator_for(SofortBuilder)
    with pytest.raises(ParameterValidationError) as exc:
        validator.validate_parameter_type("flag", "nope", {"type": (int, bool)})
    msg = str(exc.value)
    assert "flag" in msg
    assert "one of types" in msg or "'true'/'false'" in msg


def test_validate_parameter_type_tuple_with_bool_no_str_accepts_true_string():
    # ``(int, bool)`` — a raw bool isn't a match (True isn't int-compatible
    # for our purposes) but ``'true'`` / ``'false'`` still round-trip via
    # the bool-in-tuple branch and must pass silently.
    validator = _validator_for(SofortBuilder)
    validator.validate_parameter_type("flag", "true", {"type": (int, bool)})
    validator.validate_parameter_type("flag", "FALSE", {"type": (int, bool)})


def test_validate_parameter_type_tuple_without_bool_rejects_mismatch():
    validator = _validator_for(SofortBuilder)
    with pytest.raises(ParameterValidationError) as exc:
        validator.validate_parameter_type("count", "not-an-int", {"type": (int, float)})
    assert "count" in str(exc.value)
    assert "got str" in str(exc.value)


# ---------------------------------------------------------------------------
# validate_single_parameter — action lookup and disallowed keys.


def test_validate_single_parameter_rejects_unknown_key():
    validator = _validator_for(IdealBuilder)
    with pytest.raises(ParameterValidationError) as exc:
        validator.validate_single_parameter("rogue", "x", action="Pay")
    assert "rogue" in str(exc.value)
    assert exc.value.action == "Pay"


def test_validate_single_parameter_accepts_known_key_with_correct_type():
    validator = _validator_for(IdealBuilder)
    # issuer: str, known. No exception.
    validator.validate_single_parameter("issuer", "INGBNL2A", action="Pay")


# ---------------------------------------------------------------------------
# validate_required_parameters — required presence, grouped support.


def test_validate_required_parameters_returns_silently_when_present():
    validator = _validator_for(CreditcardBuilder)
    params = [Parameter(name="EncryptedCardData", value="blob")]
    validator.validate_required_parameters(params, action="PayEncrypted")


def test_validate_required_parameters_raises_required_missing_for_single_gap():
    validator = _validator_for(CreditcardBuilder)
    with pytest.raises(RequiredParameterMissingError) as exc:
        validator.validate_required_parameters([], action="PayEncrypted")
    assert exc.value.parameter_name == "encryptedcarddata"
    assert "encryptedcarddata" in str(exc.value)
    assert exc.value.service_name == "CreditCard"


def test_validate_required_parameters_raises_validation_error_for_multiple_gaps():
    validator = _validator_for(KlarnaBuilder)
    # Klarna Pay requires billingCustomer, shippingCustomer, article — all missing.
    with pytest.raises(ParameterValidationError) as exc:
        validator.validate_required_parameters([], action="Pay")
    # Multiple missing -> plain ParameterValidationError (not Required...),
    # and the message lists each missing name.
    assert not isinstance(exc.value, RequiredParameterMissingError)
    msg = str(exc.value)
    assert "billingCustomer" in msg
    assert "shippingCustomer" in msg
    assert "article" in msg


def test_validate_required_parameters_accepts_grouped_group_type_as_satisfying_requirement():
    validator = _validator_for(KlarnaBuilder)
    params = [
        Parameter(name="FirstName", value="Jane", group_type="billingCustomer"),
        Parameter(name="FirstName", value="John", group_type="shippingCustomer"),
        Parameter(name="Identifier", value="A1", group_type="article"),
    ]
    # All three required group_types are present via grouped parameters.
    validator.validate_required_parameters(params, action="Pay")


def test_validate_required_parameters_supports_dot_notation_required_keys():
    # Synthetic rule table with a dot-notation required key.
    builder = _stub_builder(
        {
            "Pay": {
                "service_parameters.issuer": {
                    "type": str,
                    "required": True,
                }
            }
        },
        service_name="dotted",
    )
    validator = ServiceParameterValidator(builder)

    with pytest.raises(RequiredParameterMissingError) as exc:
        validator.validate_required_parameters([], action="Pay")
    # The raised name is the *last* segment of the dot-notation key.
    assert exc.value.parameter_name == "issuer"

    # Providing it under the simple name satisfies the requirement.
    validator.validate_required_parameters(
        [Parameter(name="Issuer", value="INGBNL2A")], action="Pay"
    )


# ---------------------------------------------------------------------------
# validate_and_filter_parameters — filter semantics & grouped handling.


def test_filter_drops_unknown_keys_and_preserves_known_ones():
    validator = _validator_for(IdealBuilder)
    good = Parameter(name="Issuer", value="INGBNL2A")
    garbage = Parameter(name="NotARealParam", value="nope")

    result = validator.validate_and_filter_parameters([good, garbage], action="Pay")

    assert good in result
    assert garbage not in result


def test_filter_returns_empty_list_when_given_empty_list():
    validator = _validator_for(IdealBuilder)
    assert validator.validate_and_filter_parameters([], action="Pay") == []


def test_filter_drops_unknown_sofort_key():
    # ``customerbic`` is not in Sofort's allowed rule set; it must be dropped.
    validator = _validator_for(SofortBuilder)
    ok = Parameter(name="SaveToken", value="true")
    bad_type = Parameter(name="customerbic", value="INGBNL2A")  # not in allowed

    result = validator.validate_and_filter_parameters([ok, bad_type], action="Pay")
    assert ok in result
    assert bad_type not in result


def test_filter_preserves_grouped_parameters_when_group_type_is_allowed():
    validator = _validator_for(KlarnaBuilder)
    article = Parameter(name="Identifier", value="SKU-1", group_type="article", group_id="1")
    result = validator.validate_and_filter_parameters([article], action="Pay")
    assert article in result


def test_filter_drops_grouped_parameters_when_group_type_is_not_allowed():
    validator = _validator_for(IdealBuilder)
    # iDEAL Pay has no grouped params at all; ``article`` is an unknown group.
    article = Parameter(name="Identifier", value="SKU-1", group_type="article", group_id="1")
    result = validator.validate_and_filter_parameters([article], action="Pay")
    assert article not in result


def test_filter_drops_service_params_marker_when_rule_is_top_level():
    # ``issuer`` is a top-level rule on iDEAL; providing it via the
    # service_parameters marker must be dropped.
    validator = _validator_for(IdealBuilder)
    misplaced = Parameter(name="Issuer", value="INGBNL2A", group_type="__from_service_params__")
    result = validator.validate_and_filter_parameters([misplaced], action="Pay")
    assert misplaced not in result


def test_filter_drops_top_level_param_when_rule_requires_service_params():
    builder = _stub_builder(
        {
            "Pay": {
                "service_parameters.issuer": {"type": str, "required": False},
            }
        }
    )
    validator = ServiceParameterValidator(builder)

    misplaced = Parameter(name="Issuer", value="INGBNL2A")
    result = validator.validate_and_filter_parameters([misplaced], action="Pay")
    assert misplaced not in result


def test_filter_accepts_dot_notation_param_when_from_service_params():
    builder = _stub_builder(
        {
            "Pay": {
                "service_parameters.issuer": {"type": str, "required": False},
            }
        }
    )
    validator = ServiceParameterValidator(builder)

    ok = Parameter(name="Issuer", value="INGBNL2A", group_type="__from_service_params__")
    result = validator.validate_and_filter_parameters([ok], action="Pay")
    assert ok in result


def test_filter_drops_parameter_whose_value_fails_type_check():
    # A rule with type=int should reject a non-numeric string value.
    builder = _stub_builder({"Pay": {"count": {"type": int, "required": False}}})
    validator = ServiceParameterValidator(builder)

    # Parameter.value is a string; normalize_parameter_value returns it
    # unchanged (not 'true'/'false'), so the int type-check below will fail.
    bad = Parameter(name="count", value="not-an-int")
    result = validator.validate_and_filter_parameters([bad], action="Pay")
    assert bad not in result


# ---------------------------------------------------------------------------
# validate_all_parameters — strict vs filter mode.


def test_validate_all_strict_returns_params_on_success():
    validator = _validator_for(IdealBuilder)
    params = [Parameter(name="Issuer", value="INGBNL2A")]
    assert validator.validate_all_parameters(params, action="Pay", strict=True) == params


def test_validate_all_strict_raises_on_required_missing():
    validator = _validator_for(CreditcardBuilder)
    with pytest.raises(RequiredParameterMissingError):
        validator.validate_all_parameters([], action="PayEncrypted", strict=True)


def test_validate_all_strict_raises_on_unknown_param():
    validator = _validator_for(IdealBuilder)
    with pytest.raises(ParameterValidationError) as exc:
        validator.validate_all_parameters(
            [Parameter(name="Rogue", value="x")],
            action="Pay",
            strict=True,
        )
    # The error must name the offending parameter.
    assert exc.value.parameter_name == "Rogue"


def test_validate_all_strict_raises_on_type_mismatch_for_known_param():
    # Numeric-typed rule with a string value that cannot round-trip to bool.
    builder = _stub_builder({"Pay": {"count": {"type": int, "required": False}}})
    validator = ServiceParameterValidator(builder)
    with pytest.raises(ParameterValidationError):
        validator.validate_all_parameters(
            [Parameter(name="count", value="nope")],
            action="Pay",
            strict=True,
        )


def test_validate_all_non_strict_filters_invalid_and_checks_required(capsys):
    validator = _validator_for(IdealBuilder)
    good = Parameter(name="Issuer", value="INGBNL2A")
    bad = Parameter(name="Rogue", value="x")
    result = validator.validate_all_parameters([good, bad], action="Pay", strict=False)
    assert result == [good]
    # Filter prints a warning; drain it so it doesn't pollute other captures.
    capsys.readouterr()


# ---------------------------------------------------------------------------
# get_parameter_info / is_parameter_allowed / get_normalized_parameter_name.


def test_get_parameter_info_returns_rule_table_for_action():
    validator = _validator_for(CreditcardBuilder)
    info = validator.get_parameter_info("PayEncrypted")
    assert "encryptedcarddata" in info
    assert info["encryptedcarddata"]["required"] is True


def test_is_parameter_allowed_case_insensitive_and_underscore_tolerant():
    validator = _validator_for(IdealBuilder)
    assert validator.is_parameter_allowed("issuer", "Pay") is True
    assert validator.is_parameter_allowed("Issuer", "Pay") is True
    assert validator.is_parameter_allowed("Iss_uer", "Pay") is True
    assert validator.is_parameter_allowed("nope", "Pay") is False


def test_get_normalized_parameter_name_returns_empty_when_unknown():
    validator = _validator_for(IdealBuilder)
    assert validator.get_normalized_parameter_name("issuer", "Pay") == "issuer"
    assert validator.get_normalized_parameter_name("nope", "Pay") == ""


# ---------------------------------------------------------------------------
# Action-name case-insensitivity (via the builder's own rule table).


@pytest.mark.parametrize("action", ["Pay", "pay", "PAY"])
def test_action_lookup_is_case_insensitive(action):
    validator = _validator_for(IdealBuilder)
    assert validator.is_parameter_allowed("issuer", action=action) is True
    # Required-validation also honours case; ideal has no required params.
    validator.validate_required_parameters([], action=action)


@pytest.mark.parametrize("action", ["PayEncrypted", "payencrypted", "PAYENCRYPTED"])
def test_creditcard_payencrypted_action_matches_case_insensitively(action):
    validator = _validator_for(CreditcardBuilder)
    with pytest.raises(RequiredParameterMissingError):
        validator.validate_required_parameters([], action=action)


# ---------------------------------------------------------------------------
# Rule-table round-trip: every registered builder's own rules validate
# against themselves. Loads the rule table from the validator itself so
# a source edit reflects in assertions automatically.


_BUILDERS_WITH_PAY_RULES = [
    IdealBuilder,
    SofortBuilder,
    KlarnaBuilder,
    IdealQrBuilder,
]

# Subset: only builders whose Pay spec has at least one required field.
_BUILDERS_WITH_REQUIRED_PAY_PARAMS = [
    KlarnaBuilder,
]


@pytest.mark.parametrize("builder_cls", _BUILDERS_WITH_PAY_RULES)
def test_every_allowed_param_name_roundtrips_through_is_parameter_allowed(builder_cls):
    validator = _validator_for(builder_cls)
    rules = validator.get_parameter_info("Pay")
    for name in rules:
        assert validator.is_parameter_allowed(name, action="Pay") is True


@pytest.mark.parametrize("builder_cls", _BUILDERS_WITH_REQUIRED_PAY_PARAMS)
def test_every_required_param_missing_triggers_required_error(builder_cls):
    validator = _validator_for(builder_cls)
    required = {
        name for name, cfg in validator.get_parameter_info("Pay").items() if cfg.get("required")
    }
    assert required, f"{builder_cls.__name__} should have required Pay params"

    with pytest.raises(ParameterValidationError):
        validator.validate_required_parameters([], action="Pay")
