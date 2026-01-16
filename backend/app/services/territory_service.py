from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.territory import Territory
from app.models.dealer import Dealer
from app.schemas.territory import TerritoryResponse


class TerritoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_territories(self, depot_id: Optional[int] = None) -> List[TerritoryResponse]:
        """Tüm territory'leri getir (depot filtresi ile)"""
        if depot_id:
            # Bu depoya ait dealer'ların territory'lerini getir
            territories = self.db.query(Territory).join(
                Dealer, Territory.id == Dealer.territory_id
            ).filter(
                Dealer.depot_id == depot_id
            ).distinct().order_by(Territory.name).all()
            return [TerritoryResponse(id=t.id, name=t.name) for t in territories]
        else:
            # Tüm territory'leri getir
            territories = self.db.query(Territory).order_by(Territory.name).all()
            return [TerritoryResponse(id=t.id, name=t.name) for t in territories]
