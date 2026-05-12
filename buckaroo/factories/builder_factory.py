from abc import ABC, abstractmethod
from typing import Dict, Type


class BuilderFactory(ABC):
    """Abstract base class for builder factories."""

    @classmethod
    @abstractmethod
    def create_builder(cls, method: str, client):
        """
        Create a builder for the specified method.

        Args:
            method (str): The method name (e.g., 'ideal', 'subscription')
            client: The Buckaroo client instance

        Returns:
            Builder instance for the specified method

        Raises:
            ValueError: If the method is not supported
        """
        pass

    @classmethod
    @abstractmethod
    def register_method(cls, method: str, builder_class: Type) -> None:
        """
        Register a new method builder.

        Args:
            method (str): The method name
            builder_class (Type): The builder class for this method
        """
        pass

    @classmethod
    @abstractmethod
    def get_available_methods(cls) -> list:
        """
        Get a list of all available methods.

        Returns:
            list: List of available method names
        """
        pass

    @classmethod
    @abstractmethod
    def is_method_supported(cls, method: str) -> bool:
        """
        Check if a method is supported.

        Args:
            method (str): The method name

        Returns:
            bool: True if the method is supported, False otherwise
        """
        pass

    @classmethod
    @abstractmethod
    def detect_method_from_payload(cls, payload: Dict) -> str:
        """
        Detect the method from payload parameters.

        Args:
            payload (Dict): Parameters dictionary

        Returns:
            str: Detected method name

        Raises:
            ValueError: If method cannot be determined from payload
        """
        pass
