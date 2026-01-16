from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.services.dealer_service import DealerService
from app.schemas.dealer import DealerResponse, DealerSearchResponse

router = APIRouter()


@router.get("/", response_model=list[DealerSearchResponse])
async def search_dealers(
    territory: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    depot_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Bayileri ara (depot filtresi ile)"""
    dealer_service = DealerService(db)
    
    # Depot filtresi: Kullanıcının depot_id'si varsa ve parametre yoksa onu kullan
    if not depot_id and current_user.get("depot_id"):
        depot_id = current_user["depot_id"]
    
    return dealer_service.search_dealers(territory=territory, search_term=search, depot_id=depot_id)


@router.get("/{code}", response_model=DealerResponse)
async def get_dealer_by_code(
    code: str,
    depot_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Bayi bilgilerini getir (depot filtresi ile)"""
    dealer_service = DealerService(db)
    
    # Depot filtresi: Kullanıcının depot_id'si varsa ve parametre yoksa onu kullan
    if not depot_id and current_user.get("depot_id"):
        depot_id = current_user["depot_id"]
    
    dealer = dealer_service.get_dealer_by_code(code, depot_id=depot_id)
    
    if not dealer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bayi bulunamadı"
        )
    
    return dealer
