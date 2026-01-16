from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.services.territory_service import TerritoryService
from app.schemas.territory import TerritoryResponse

router = APIRouter()


@router.get("/", response_model=list[TerritoryResponse])
async def get_territories(
    depot_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService.get_current_user)
):
    """Tüm territory'leri getir (depot filtresi ile)"""
    territory_service = TerritoryService(db)
    
    # Depot filtresi: Kullanıcının depot_id'si varsa ve parametre yoksa onu kullan
    user_depot_ids = current_user.get("depot_ids", [])
    if not user_depot_ids and current_user.get("depot_id"):
        user_depot_ids = [current_user["depot_id"]]
    
    # Eğer parametre olarak depot_id verilmişse, sadece o depoyu kullan
    if depot_id:
        # Admin ise tüm depoları görebilir, diğerleri sadece kendi depolarını
        if current_user["role"] == "admin" or depot_id in user_depot_ids:
            return territory_service.get_all_territories(depot_id=depot_id)
        else:
            # Kullanıcı kendi deposu dışında bir depo seçemez
            return []
    
    # Admin ise tüm territory'leri göster, diğerleri sadece kendi depolarındakileri
    if current_user["role"] == "admin":
        return territory_service.get_all_territories()
    else:
        # Kullanıcının depolarındaki territory'leri getir
        all_territories = []
        for user_depot_id in user_depot_ids:
            territories = territory_service.get_all_territories(depot_id=user_depot_id)
            # Duplicate'leri önlemek için
            for t in territories:
                if t not in all_territories:
                    all_territories.append(t)
        return all_territories
