from typing import Dict, Type
import logging

from .builder_factory import BuilderFactory
from buckaroo.builders.solutions.subscription_builder import SubscriptionBuilder
from buckaroo.builders.solutions.emandate_builder import EmandateB2BBuilder, EmandateBuilder
from buckaroo.builders.solutions.marketplaces_builder import MarketplacesBuilder
from buckaroo.builders.solutions.credit_management_builder import CreditManagementBuilder
from buckaroo.builders.solutions.default_builder import DefaultBuilder
from buckaroo.builders.solutions.solution_builder import SolutionBuilder


class SolutionMethodFactory(BuilderFactory):
    """Factory for creating payment method builders."""

    # Registry of available solution methods
    _solution_methods: Dict[str, Type[SolutionBuilder]] = {
        "subscription": SubscriptionBuilder,
        "emandate": EmandateBuilder,
        "emandateb2b": EmandateB2BBuilder,
        "marketplaces": MarketplacesBuilder,
        "creditmanagement": CreditManagementBuilder,
    }

    @classmethod
    def create_builder(cls, method: str, client) -> SolutionBuilder:
        """
        Create a payment builder for the specified method.

        Args:
            method (str): The payment method name (e.g., 'subscriptions', 'creditmanagement')
            client: The Buckaroo client instance

        Returns:
            SolutionBuilder: A builder instance for the specified payment method

        Raises:
            ValueError: If the payment method is not supported
        """
        method = method.lower()

        if method not in cls._solution_methods:
            available_methods = ", ".join(cls._solution_methods.keys())
            logging.warning(
                f"Unsupported payment method: {method}. "
                f"Available methods: {available_methods}. "
                f"Using DefaultBuilder as fallback."
            )
            # Use DefaultBuilder as fallback
            return DefaultBuilder(client)

        builder_class = cls._solution_methods[method]
        return builder_class(client)

    @classmethod
    def register_method(cls, method: str, builder_class: Type[SolutionBuilder]) -> None:
        """
        Register a new solution method builder.

        Args:
            method (str): The solution method name
            builder_class (Type[PaymentBuilder]): The builder class for this method
        """
        cls._solution_methods[method.lower()] = builder_class

    @classmethod
    def get_available_methods(cls) -> list:
        """
        Get a list of all available solution methods.

        Returns:
            list: List of available solution method names
        """
        return list(cls._solution_methods.keys())

    @classmethod
    def is_method_supported(cls, method: str) -> bool:
        """
        Check if a solution method is supported.

        Args:
            method (str): The solution method name

        Returns:
            bool: True if the method is supported, False otherwise
        """
        return method.lower() in cls._solution_methods

    @classmethod
    def detect_method_from_payload(cls, payload: Dict) -> str:
        """
        Detect the payment method from payload parameters.

        Args:
            payload (Dict): Payment parameters dictionary

        Returns:
            str: Detected payment method name

        Raises:
            ValueError: If payment method cannot be determined from payload
        """
        # Check for explicit payment method in payload
        if "method" in payload:
            return payload["method"].lower()

        return "default"
