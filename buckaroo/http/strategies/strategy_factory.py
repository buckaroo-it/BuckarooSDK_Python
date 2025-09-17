"""
HTTP Strategy Factory for Buckaroo SDK.

This module provides automatic selection of the best available HTTP strategy.
"""

from typing import Optional, List, Type
from .http_strategy import HttpStrategy
from .requests_strategy import RequestsStrategy
from .curl_strategy import CurlStrategy


class HttpStrategyFactory:
    """
    Factory for creating HTTP strategy instances.
    
    This factory automatically selects the best available HTTP strategy
    based on what's available on the system.
    """
    
    # Order of preference for strategies
    _STRATEGY_CLASSES: List[Type[HttpStrategy]] = [
        RequestsStrategy,  # Preferred: Full-featured with retry logic
        CurlStrategy,      # Fallback: No external dependencies
    ]
    
    @classmethod
    def create_strategy(cls, preferred_strategy: Optional[str] = None) -> HttpStrategy:
        """
        Create an HTTP strategy instance.
        
        Args:
            preferred_strategy: Name of preferred strategy ('requests' or 'curl')
                               If None, will auto-select the best available strategy
                               
        Returns:
            HttpStrategy: Strategy instance
            
        Raises:
            RuntimeError: If no HTTP strategy is available
        """
        # If specific strategy requested, try to use it
        if preferred_strategy:
            strategy = cls._create_named_strategy(preferred_strategy)
            if strategy and strategy.is_available():
                return strategy
            else:
                available_strategies = cls.get_available_strategies()
                raise RuntimeError(
                    f"Requested HTTP strategy '{preferred_strategy}' is not available. "
                    f"Available strategies: {available_strategies}"
                )
        
        # Auto-select best available strategy
        for strategy_class in cls._STRATEGY_CLASSES:
            strategy = strategy_class()
            if strategy.is_available():
                return strategy
        
        # No strategy available
        raise RuntimeError(
            "No HTTP strategy is available. Please install 'requests' library "
            "or ensure 'curl' command is available on your system."
        )
    
    @classmethod
    def _create_named_strategy(cls, name: str) -> Optional[HttpStrategy]:
        """
        Create a strategy by name.
        
        Args:
            name: Strategy name
            
        Returns:
            HttpStrategy instance or None if not found
        """
        strategy_map = {
            'requests': RequestsStrategy,
            'curl': CurlStrategy,
        }
        
        strategy_class = strategy_map.get(name.lower())
        return strategy_class() if strategy_class else None
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """
        Get list of available strategy names.
        
        Returns:
            List[str]: Names of available strategies
        """
        available = []
        for strategy_class in cls._STRATEGY_CLASSES:
            strategy = strategy_class()
            if strategy.is_available():
                available.append(strategy.get_name())
        return available
    
    @classmethod
    def is_strategy_available(cls, name: str) -> bool:
        """
        Check if a specific strategy is available.
        
        Args:
            name: Strategy name
            
        Returns:
            bool: True if strategy is available
        """
        strategy = cls._create_named_strategy(name)
        return strategy.is_available() if strategy else False