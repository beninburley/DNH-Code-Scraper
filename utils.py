"""Utility functions for rate limiting, error handling, and helpers."""

import time
import functools
from typing import Callable, Any
import config


def rate_limit(func: Callable) -> Callable:
    """Decorator to add rate limiting to functions."""
    last_called = [0.0]
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        elapsed = time.time() - last_called[0]
        left_to_wait = config.REQUEST_DELAY - elapsed
        
        if left_to_wait > 0:
            time.sleep(left_to_wait)
        
        ret = func(*args, **kwargs)
        last_called[0] = time.time()
        return ret
    
    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 2.0):
    """Decorator to retry function on failure."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (attempt + 1)
                        print(f"  ⚠️  Attempt {attempt + 1} failed: {e}")
                        print(f"  🔄 Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"  ❌ All {max_retries} attempts failed")
            
            raise last_exception
        
        return wrapper
    return decorator


def extract_state_from_url(url: str) -> str:
    """Extract state abbreviation from URL if possible."""
    import re
    
    # Common patterns in Municode URLs
    patterns = [
        r'/([A-Z]{2})/',  # /TX/
        r'_([A-Z]{2})_',  # _CA_
        r'-([A-Z]{2})-',  # -NY-
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return 'Unknown'


def extract_city_from_text(text: str) -> str:
    """Clean up city name from link text."""
    import re
    
    # Remove common prefixes/suffixes
    text = re.sub(r'\s*-\s*Code\s+of\s+Ordinances.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*Municipal\s+Code.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*City\s+of\s+', '', text, flags=re.IGNORECASE)
    
    return text.strip()


class ProgressTracker:
    """Track and display progress of scraping operation."""
    
    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.successful = 0
        self.failed = 0
        self.with_ethics = 0
        self.without_ethics = 0
    
    def update(self, success: bool, has_ethics: bool):
        """Update progress counters."""
        self.completed += 1
        
        if success:
            self.successful += 1
            if has_ethics:
                self.with_ethics += 1
            else:
                self.without_ethics += 1
        else:
            self.failed += 1
    
    def print_status(self):
        """Print current progress status."""
        percent = (self.completed / self.total * 100) if self.total > 0 else 0
        print(f"\n{'='*60}")
        print(f"Progress: {self.completed}/{self.total} ({percent:.1f}%)")
        print(f"  ✅ Successful: {self.successful}")
        print(f"  ❌ Failed: {self.failed}")
        print(f"  📄 With ethics codes: {self.with_ethics}")
        print(f"  ℹ️  Without ethics codes: {self.without_ethics}")
        print(f"{'='*60}\n")


if __name__ == '__main__':
    # Test utilities
    
    # Test rate limiting
    @rate_limit
    def test_func():
        print(f"Called at {time.time()}")
        return "success"
    
    print("Testing rate limiting (should have delays):")
    for i in range(3):
        test_func()
    
    # Test retry
    @retry_on_failure(max_retries=3, delay=0.5)
    def failing_func():
        print("Attempting...")
        raise ValueError("Test error")
    
    print("\nTesting retry logic:")
    try:
        failing_func()
    except ValueError:
        print("Function failed as expected")
    
    # Test progress tracker
    print("\nTesting progress tracker:")
    tracker = ProgressTracker(10)
    tracker.update(success=True, has_ethics=True)
    tracker.update(success=True, has_ethics=False)
    tracker.update(success=False, has_ethics=False)
    tracker.print_status()
