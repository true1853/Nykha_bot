"""
Performance optimizations and utilities for FarnPathBot.
"""
import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional
import time

logger = logging.getLogger(__name__)

def async_timer(func: Callable) -> Callable:
    """Decorator to measure async function execution time."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper

def cache_result(ttl: int = 300):
    """Simple in-memory cache decorator with TTL."""
    def decorator(func: Callable) -> Callable:
        cache: Dict[str, tuple] = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Create cache key from args and kwargs
            key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Check if cached result is still valid
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
                else:
                    del cache[key]
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache[key] = (result, time.time())
            logger.debug(f"Cached result for {func.__name__}")
            return result
        
        return wrapper
    return decorator

class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self) -> bool:
        """Acquire permission to make a call."""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            # Calculate wait time
            oldest_call = min(self.calls)
            wait_time = self.time_window - (now - oldest_call)
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                return await self.acquire()
        
        self.calls.append(now)
        return True

# Global rate limiters
geocoding_limiter = RateLimiter(max_calls=10, time_window=60)  # 10 calls per minute
api_limiter = RateLimiter(max_calls=100, time_window=60)  # 100 calls per minute

class PerformanceMonitor:
    """Monitor performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self.start_times: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration."""
        if operation not in self.start_times:
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append(duration)
        del self.start_times[operation]
        
        return duration
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        if operation not in self.metrics or not self.metrics[operation]:
            return {}
        
        times = self.metrics[operation]
        return {
            'count': len(times),
            'avg': sum(times) / len(times),
            'min': min(times),
            'max': max(times),
            'total': sum(times)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations."""
        return {op: self.get_stats(op) for op in self.metrics}

# Global performance monitor
perf_monitor = PerformanceMonitor()

def monitor_performance(operation: str):
    """Decorator to monitor function performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            perf_monitor.start_timer(operation)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = perf_monitor.end_timer(operation)
                logger.debug(f"{operation} completed in {duration:.3f}s")
        return wrapper
    return decorator

# Error handling improvements
class BotError(Exception):
    """Base exception for bot errors."""
    pass

class DatabaseError(BotError):
    """Database related errors."""
    pass

class ValidationError(BotError):
    """Data validation errors."""
    pass

def handle_errors(func: Callable) -> Callable:
    """Decorator for consistent error handling."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except DatabaseError as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            return None
        except ValidationError as e:
            logger.error(f"Validation error in {func.__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            return None
    return wrapper
