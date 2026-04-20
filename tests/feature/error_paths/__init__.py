"""HTTP error-path feature tests.

These tests exercise only ``create_payment("ideal", ...)`` because error
mapping (auth failures, server errors, malformed bodies) lives in the HTTP
client and is method-agnostic. Per-method duplication would be wasteful;
a single representative method covers the contract.
"""
