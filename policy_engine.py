from typing import Dict, List, Optional, Set  # Type hints
import os  # For environment variables
from datetime import datetime  # For time-based operations
from prometheus_client import Counter, Gauge, Histogram  # For metrics collection

class PolicyEngine:
    def __init__(self):
        """
        Initialize the policy engine with API keys from environment variables.
        Does not hardcode any sensitive data.
        """
        # Get API keys from environment variables
        self.api_keys = {}
        
        # Add the consumer key with its policies
        consumer_key = os.getenv("CALCULATOR_CONSUMER_API_KEY", "")
        if consumer_key:
            self.api_keys[consumer_key] = {
                "service": "calculator_consumer",  # Service identifier
                "permissions": {  # Allowed API endpoints
                    "store_calculation": True,
                    "get_calculations": True
                },
                "rate_limit": 100,  # Requests per minute
                "max_input_value": 1000  # Maximum allowed input value
            }
        
        # Add the server key with its policies
        server_key = os.getenv("CALCULATOR_SERVER_API_KEY", "")
        if server_key:
            self.api_keys[server_key] = {
                "service": "calculator_server",
                "permissions": {
                    "store_calculation": True,
                    "get_calculations": False  # Server can't read calculations
                },
                "rate_limit": 200,  # Higher rate limit for server
                "max_input_value": 10000  # Higher input limit for server
            }
            
        # Track rate limiting
        self.request_counts = {}  # Tracks number of requests per API key
        self.last_reset = datetime.now()  # Timestamp of last rate limit reset
        
        # Define Prometheus metrics for policy engine
        self.policy_violation_counter = Counter(
            'policy_violation_total',
            'Number of policy violations',
            ['violation_type', 'service']
        )
        
        self.rate_limit_usage = Gauge(
            'rate_limit_usage_percent',
            'Current rate limit usage percentage',
            ['service']
        )
        
        self.api_request_counter = Counter(
            'api_requests_total',
            'Total number of API requests',
            ['service', 'endpoint', 'status']
        )
        
        self.input_value_histogram = Histogram(
            'input_value_size',
            'Size of input values',
            ['service'],
            buckets=[10, 50, 100, 500, 1000, 5000, 10000]  # Value size buckets
        )
    
    def is_valid_api_key(self, api_key: Optional[str]) -> bool:
        """
        Check if the API key is valid
        
        Args:
            api_key: The API key to validate
            
        Returns:
            True if API key is registered, False otherwise
        """
        if not api_key:
            # Record violation for missing API key
            self.policy_violation_counter.labels(
                violation_type='missing_api_key',
                service='unknown'
            ).inc()
            return False
        
        is_valid = api_key in self.api_keys
        if not is_valid:
            # Record violation for invalid API key
            self.policy_violation_counter.labels(
                violation_type='invalid_api_key',
                service='unknown'
            ).inc()
        else:
            # Record successful API key validation
            service_name = self.api_keys[api_key].get('service', 'unknown')
            self.api_request_counter.labels(
                service=service_name,
                endpoint='api_key_validation',
                status='success'
            ).inc()
            
        return is_valid
    
    def check_rate_limit(self, api_key: str) -> bool:
        """
        Check if the API key is within rate limits
        
        Args:
            api_key: The API key to check
            
        Returns:
            True if request is within rate limits, False otherwise
        """
        # Reset counters if a minute has passed
        now = datetime.now()
        if (now - self.last_reset).seconds > 60:
            self.request_counts = {}  # Clear all counters
            self.last_reset = now
        
        # Initialize counter if needed
        if api_key not in self.request_counts:
            self.request_counts[api_key] = 0
        
        # Check rate limit
        service_info = self.api_keys.get(api_key, {})
        service_name = service_info.get("service", "unknown")
        rate_limit = service_info.get("rate_limit", 100)  # Default rate limit
        
        # Calculate and record rate limit usage percentage
        usage_percent = (self.request_counts[api_key] / rate_limit) * 100 if rate_limit > 0 else 0
        self.rate_limit_usage.labels(service=service_name).set(usage_percent)
        
        if self.request_counts[api_key] >= rate_limit:
            # Record rate limit violation
            self.policy_violation_counter.labels(
                violation_type='rate_limit_exceeded',
                service=service_name
            ).inc()
            return False
        
        # Increment counter
        self.request_counts[api_key] += 1
        return True
    
    def can_access_endpoint(self, api_key: str, endpoint: str) -> bool:
        """
        Check if the service can access a specific endpoint
        
        Args:
            api_key: The API key of the service
            endpoint: The endpoint being accessed
            
        Returns:
            True if service has permission for the endpoint, False otherwise
        """
        if not self.is_valid_api_key(api_key):
            return False
            
        service_info = self.api_keys.get(api_key, {})
        service_name = service_info.get("service", "unknown")
        permissions = service_info.get("permissions", {})
        
        can_access = permissions.get(endpoint, False)
        
        if can_access:
            # Record successful endpoint access
            self.api_request_counter.labels(
                service=service_name,
                endpoint=endpoint,
                status='success'
            ).inc()
        else:
            # Record unauthorized endpoint access
            self.policy_violation_counter.labels(
                violation_type='unauthorized_endpoint',
                service=service_name
            ).inc()
            self.api_request_counter.labels(
                service=service_name,
                endpoint=endpoint,
                status='denied'
            ).inc()
            
        return can_access
    
    def validate_calculation_input(self, api_key: str, num1: float, num2: float) -> bool:
        """
        Validate that input numbers are within the service's allowed limits
        
        Args:
            api_key: The API key of the service
            num1: First number in calculation
            num2: Second number in calculation
            
        Returns:
            True if inputs are within allowed limits, False otherwise
        """
        service_info = self.api_keys.get(api_key, {})
        service_name = service_info.get("service", "unknown")
        max_value = service_info.get("max_input_value", 100)
        
        # Record input value sizes in histogram
        self.input_value_histogram.labels(service=service_name).observe(abs(num1))
        self.input_value_histogram.labels(service=service_name).observe(abs(num2))
        
        is_valid = abs(num1) <= max_value and abs(num2) <= max_value
        
        if not is_valid:
            # Record input validation violation
            self.policy_violation_counter.labels(
                violation_type='input_value_exceeded',
                service=service_name
            ).inc()
            
        return is_valid

# Global instance to be imported by other modules
policy_engine = PolicyEngine()