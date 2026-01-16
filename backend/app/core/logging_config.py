import logging
import sys
from typing import Any
from app.core.config import settings


def setup_logging() -> None:
    """Production için logging yapılandırması"""
    log_level = getattr(settings, 'LOG_LEVEL', 'INFO').upper()
    
    # Log formatı
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Root logger yapılandırması
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # SQLAlchemy log seviyesini düşür (production'da çok verbose)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    
    # Uvicorn access log'larını kontrol et
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging yapılandırıldı - Seviye: {log_level}")


def get_logger(name: str) -> logging.Logger:
    """Logger instance'ı al"""
    return logging.getLogger(name)
