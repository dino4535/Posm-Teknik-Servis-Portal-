from fastapi import Request
from typing import Optional


def get_client_ip(request: Request) -> Optional[str]:
    """
    Gerçek client IP adresini al (reverse proxy arkasında çalışıyorsa)
    X-Forwarded-For header'ını kontrol eder, yoksa request.client.host kullanır
    """
    # X-Forwarded-For header'ını kontrol et (reverse proxy arkasındaysa)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For: client, proxy1, proxy2 formatında olabilir
        # İlk IP adresi gerçek client IP'sidir
        ip = forwarded_for.split(",")[0].strip()
        if ip:
            return ip
    
    # X-Real-IP header'ını kontrol et (nginx gibi bazı proxy'ler kullanır)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback: request.client.host
    if request.client:
        return request.client.host
    
    return None
