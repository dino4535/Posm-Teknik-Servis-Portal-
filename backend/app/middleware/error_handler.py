from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from app.core.config import settings

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """Global error handler middleware"""
    try:
        response = await call_next(request)
        return response
    except RequestValidationError as e:
        # Validation hataları - production'da detayları gizle
        logger.warning(f"Validation error: {e.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Geçersiz istek parametreleri",
                "errors": e.errors() if getattr(settings, 'DEBUG', False) else None
            }
        )
    except StarletteHTTPException as e:
        # HTTP exception'lar
        logger.warning(f"HTTP exception: {e.status_code} - {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    except Exception as e:
        # Beklenmeyen hatalar
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        
        # Production'da detaylı hata mesajı gösterme
        error_detail = "Bir hata oluştu" if not getattr(settings, 'DEBUG', False) else str(e)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": error_detail,
                "traceback": traceback.format_exc() if getattr(settings, 'DEBUG', False) else None
            }
        )
