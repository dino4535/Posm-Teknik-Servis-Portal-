from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.dealer import Dealer
from app.models.territory import Territory
from app.schemas.dealer import DealerResponse, DealerSearchResponse


class DealerService:
    def __init__(self, db: Session):
        self.db = db

    def search_dealers(self, territory: Optional[str] = None, search_term: Optional[str] = None, depot_id: Optional[int] = None) -> List[DealerSearchResponse]:
        """Bayileri ara (depot filtresi ile)"""
        query = self.db.query(Dealer)
        
        # Depot filtresi
        if depot_id:
            query = query.filter(Dealer.depot_id == depot_id)
        
        # Territory filtresi
        if territory:
            territory_obj = self.db.query(Territory).filter(Territory.name == territory).first()
            if territory_obj:
                query = query.filter(Dealer.territory_id == territory_obj.id)
        
        # Arama terimi filtresi
        if search_term:
            search_lower = search_term.lower()
            query = query.filter(
                or_(
                    Dealer.code.ilike(f"%{search_lower}%"),
                    Dealer.name.ilike(f"%{search_lower}%")
                )
            )
        
        dealers = query.all()
        
        results = []
        for dealer in dealers:
            territory_name = None
            if dealer.territory:
                territory_name = dealer.territory.name
            
            results.append(DealerSearchResponse(
                territory=territory_name,
                bayiKodu=dealer.code,
                bayiAdi=dealer.name
            ))
        
        return results

    def get_dealer_by_code(self, code: str, depot_id: Optional[int] = None) -> Optional[DealerResponse]:
        """Bayi bilgilerini kod ile getir (depot filtresi ile)"""
        query = self.db.query(Dealer).filter(Dealer.code == code)
        
        if depot_id:
            query = query.filter(Dealer.depot_id == depot_id)
        
        dealer = query.first()
        
        if not dealer:
            return None
        
        return DealerResponse(
            id=dealer.id,
            territory_id=dealer.territory_id,
            depot_id=dealer.depot_id,
            code=dealer.code,
            name=dealer.name,
            latitude=dealer.latitude,
            longitude=dealer.longitude
        )
