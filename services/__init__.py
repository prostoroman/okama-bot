"""
Okama Finance Bot Services Package

This package contains all the specialized services for financial analysis:
- CorrelationService: Asset correlation analysis
- FrontierService: Efficient frontier generation
- ComparisonService: Asset comparison
- PensionService: Pension portfolio analysis
- MonteCarloService: Monte Carlo forecasting
- AllocationService: Asset allocation analysis
- OkamaServiceV2: Main service coordinator
"""

from .correlation_service import CorrelationService
from .frontier_service import FrontierService
from .comparison_service import ComparisonService
from .pension_service import PensionService
from .monte_carlo_service import MonteCarloService
from .allocation_service import AllocationService
from .okama_service import OkamaServiceV2

__all__ = [
    'CorrelationService',
    'FrontierService', 
    'ComparisonService',
    'PensionService',
    'MonteCarloService',
    'AllocationService',
    'OkamaServiceV2'
]

__version__ = '2.0.0'
