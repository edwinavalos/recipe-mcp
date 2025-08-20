"""Compliance framework for recipe extraction with rate limiting and legal oversight."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Callable, Awaitable
from functools import wraps
import httpx
from .models import ComplianceStatus, ComplianceInfo

logger = logging.getLogger(__name__)


class ComplianceConfig:
    """Configuration for compliance monitoring."""
    
    DAILY_EXTRACTION_LIMIT = 50
    RATE_LIMIT_WINDOW = 60  # seconds
    MAX_REQUESTS_PER_WINDOW = 10
    RESPECT_ROBOTS_TXT = True
    USER_AGENT = "Recipe MCP Server/1.0 (Educational Use)"


class ComplianceMonitor:
    """Monitors and enforces compliance during recipe extraction."""
    
    def __init__(self, config: Optional[ComplianceConfig] = None):
        self.config = config or ComplianceConfig()
        self._daily_usage: Dict[str, int] = {}
        self._rate_limits: Dict[str, list] = {}
        self._session_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        
    async def check_compliance(self, url: str) -> ComplianceInfo:
        """Check if extraction is compliant with rate limits and policies."""
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Check daily usage
        daily_count = self._daily_usage.get(today, 0)
        if daily_count >= self.config.DAILY_EXTRACTION_LIMIT:
            return ComplianceInfo(
                status=ComplianceStatus.RATE_LIMITED,
                daily_usage_count=daily_count,
                daily_limit=self.config.DAILY_EXTRACTION_LIMIT,
                session_id=self._session_id,
                rate_limit_reset=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0) + timedelta(days=1),
                warnings=["Daily extraction limit reached"]
            )
        
        # Check rate limiting
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=self.config.RATE_LIMIT_WINDOW)
        
        # Clean old requests
        if today in self._rate_limits:
            self._rate_limits[today] = [
                req_time for req_time in self._rate_limits[today]
                if req_time > window_start
            ]
            
            if len(self._rate_limits[today]) >= self.config.MAX_REQUESTS_PER_WINDOW:
                return ComplianceInfo(
                    status=ComplianceStatus.RATE_LIMITED,
                    daily_usage_count=daily_count,
                    daily_limit=self.config.DAILY_EXTRACTION_LIMIT,
                    session_id=self._session_id,
                    rate_limit_reset=now + timedelta(seconds=self.config.RATE_LIMIT_WINDOW),
                    warnings=["Rate limit exceeded"]
                )
        
        return ComplianceInfo(
            status=ComplianceStatus.COMPLIANT,
            daily_usage_count=daily_count,
            daily_limit=self.config.DAILY_EXTRACTION_LIMIT,
            session_id=self._session_id
        )
    
    async def record_extraction(self, url: str) -> None:
        """Record an extraction attempt for compliance tracking."""
        today = datetime.now(timezone.utc).date().isoformat()
        now = datetime.now(timezone.utc)
        
        # Update daily usage
        self._daily_usage[today] = self._daily_usage.get(today, 0) + 1
        
        # Update rate limiting
        if today not in self._rate_limits:
            self._rate_limits[today] = []
        self._rate_limits[today].append(now)
        
        logger.info(f"Recorded extraction for {url}, daily usage: {self._daily_usage[today]}")
    
    async def get_daily_usage(self) -> Dict[str, Any]:
        """Get current daily usage statistics."""
        today = datetime.now(timezone.utc).date().isoformat()
        return {
            "date": today,
            "usage_count": self._daily_usage.get(today, 0),
            "daily_limit": self.config.DAILY_EXTRACTION_LIMIT,
            "remaining": max(0, self.config.DAILY_EXTRACTION_LIMIT - self._daily_usage.get(today, 0)),
            "session_id": self._session_id
        }


class ComplianceHTTPSession:
    """HTTP session with compliance features for respectful web scraping."""
    
    def __init__(self, config: Optional[ComplianceConfig] = None):
        self.config = config or ComplianceConfig()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            headers={"User-Agent": self.config.USER_AGENT},
            timeout=30.0
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make a compliant GET request."""
        if not self._client:
            raise RuntimeError("Session not initialized")
        
        # Add delay to be respectful
        await asyncio.sleep(1.0)
        
        logger.info(f"Making compliant request to {url}")
        return await self._client.get(url, **kwargs)


# Global compliance monitor instance
_compliance_monitor = ComplianceMonitor()


def ensure_compliance():
    """Decorator to ensure compliance for extraction functions."""
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract URL from arguments
            url = None
            if args and isinstance(args[0], str) and args[0].startswith('http'):
                url = args[0]
            elif 'url' in kwargs:
                url = kwargs['url']
            
            if url:
                # Check compliance before extraction
                compliance_info = await _compliance_monitor.check_compliance(url)
                if compliance_info.status != ComplianceStatus.COMPLIANT:
                    # Return result with compliance error
                    from .models import ExtractionResult
                    return ExtractionResult(
                        success=False,
                        error=f"Compliance check failed: {compliance_info.status.value}",
                        extraction_time=0.0,
                        compliance_info=compliance_info
                    )
                
                # Record the extraction attempt
                await _compliance_monitor.record_extraction(url)
            
            # Execute the original function
            result = await func(*args, **kwargs)
            
            # Add compliance info to result if it's an ExtractionResult
            if hasattr(result, 'compliance_info') and url:
                compliance_info = await _compliance_monitor.check_compliance(url)
                result.compliance_info = compliance_info
            
            return result
        return wrapper
    return decorator


async def get_compliance_status() -> Dict[str, Any]:
    """Get current compliance status."""
    return await _compliance_monitor.get_daily_usage()


async def get_daily_usage() -> Dict[str, Any]:
    """Get daily usage statistics."""
    return await _compliance_monitor.get_daily_usage()