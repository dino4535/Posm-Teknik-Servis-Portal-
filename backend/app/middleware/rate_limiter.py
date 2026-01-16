from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
import time
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware - IP bazlı"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)  # IP -> [timestamp1, timestamp2, ...]
        self.cleanup_interval = timedelta(minutes=5)
        self.last_cleanup = datetime.now()
    
    def _cleanup_old_requests(self):
        """Eski request kayıtlarını temizle"""
        now = datetime.now()
        if now - self.last_cleanup > self.cleanup_interval:
            cutoff = now - timedelta(minutes=1)
            for ip in list(self.requests.keys()):
                self.requests[ip] = [
                    ts for ts in self.requests[ip] 
                    if ts > cutoff
                ]
                if not self.requests[ip]:
                    del self.requests[ip]
            self.last_cleanup = now
    
    async def dispatch(self, request: Request, call_next):
        # Rate limiting aktif değilse geç
        if not getattr(settings, 'RATE_LIMIT_ENABLED', False):
            return await call_next(request)
        
        # Health check ve static files için rate limiting yok
        if request.url.path in ['/health', '/'] or request.url.path.startswith('/uploads'):
            return await call_next(request)
        
        # Client IP'yi al (gerçek ISP IP'si)
        from app.utils.ip_helper import get_client_ip
        client_ip = get_client_ip(request) or "unknown"
        
        # Eski kayıtları temizle
        self._cleanup_old_requests()
        
        # Son 1 dakikadaki request sayısını kontrol et
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        # Bu IP'nin son 1 dakikadaki request'lerini filtrele
        recent_requests = [
            ts for ts in self.requests[client_ip]
            if ts > cutoff
        ]
        
        # Rate limit kontrolü
        requests_per_minute = getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60)
        if len(recent_requests) >= requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Çok fazla istek. Lütfen {requests_per_minute} istek/dakika limitine dikkat edin.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Request'i kaydet
        self.requests[client_ip].append(now)
        
        # Response'u al
        response = await call_next(request)
        
        # Rate limit bilgisini header'a ekle
        remaining = requests_per_minute - len(recent_requests) - 1
        response.headers["X-RateLimit-Limit"] = str(requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(minutes=1)).timestamp()))
        
        return response
