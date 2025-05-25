from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ResourceCost:
    """Represents the cost information for a single resource."""
    resource_type: str
    resource_id: str
    hourly_cost: float
    monthly_cost: float
    currency: str = "USD"
    usage_type: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = None
    pricing_model: Optional[str] = None  # "fixed", "usage_based", "free"
    pricing_details: Optional[str] = None  # Human-readable pricing explanation

class CostEstimator(ABC):
    """Abstract base class for cost estimators."""
    
    @abstractmethod
    def get_resource_cost(self, resource_type: str, resource_properties: Dict[str, Any]) -> ResourceCost:
        """Get cost information for a single resource."""
        pass
    
    @abstractmethod
    def get_supported_resources(self) -> List[str]:
        """Get list of supported resource types."""
        pass
    
    @abstractmethod
    def is_resource_supported(self, resource_type: str) -> bool:
        """Check if a resource type is supported."""
        pass

class CostEstimationError(Exception):
    """Base exception for cost estimation errors."""
    pass

class ResourceNotSupportedError(CostEstimationError):
    """Raised when a resource type is not supported."""
    pass

class PricingDataError(CostEstimationError):
    """Raised when there's an error fetching pricing data."""
    pass

def format_cost(cost: float, currency: str = "USD") -> str:
    """Format cost with appropriate currency symbol and decimal places."""
    if currency == "USD":
        return f"${cost:.2f}"
    return f"{cost:.2f} {currency}" 