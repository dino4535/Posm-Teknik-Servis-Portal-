from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.posm import Posm
from app.models.posm_transfer import PosmTransfer
from app.schemas.posm import (
    PosmResponse, PosmCreateRequest, PosmUpdateRequest, 
    PosmStockResponse, PosmTransferRequest, PosmTransferResponse
)


class PosmService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_posm(self, depot_id: Optional[int] = None) -> List[PosmResponse]:
        """Tüm POSM'leri getir (depot filtresi ile)"""
        query = self.db.query(Posm)
        
        if depot_id:
            query = query.filter(Posm.depot_id == depot_id)
        
        posms = query.order_by(Posm.name).all()
        return [PosmResponse(
            id=p.id,
            name=p.name,
            depot_id=p.depot_id,
            ready_count=p.ready_count,
            repair_pending_count=p.repair_pending_count
        ) for p in posms]

    def get_posm_by_id(self, posm_id: int) -> Optional[PosmResponse]:
        """POSM'i ID ile getir"""
        posm = self.db.query(Posm).filter(Posm.id == posm_id).first()
        if not posm:
            return None
        
        return PosmResponse(
            id=posm.id,
            name=posm.name,
            depot_id=posm.depot_id,
            ready_count=posm.ready_count,
            repair_pending_count=posm.repair_pending_count
        )

    def get_posm_by_name(self, name: str, depot_id: Optional[int] = None) -> Optional[PosmResponse]:
        """POSM'i isim ile getir (depot bazında)"""
        query = self.db.query(Posm).filter(Posm.name == name)
        if depot_id:
            query = query.filter(Posm.depot_id == depot_id)
        posm = query.first()
        if not posm:
            return None
        
        return PosmResponse(
            id=posm.id,
            name=posm.name,
            depot_id=posm.depot_id,
            ready_count=posm.ready_count,
            repair_pending_count=posm.repair_pending_count
        )

    def get_posm_stock(self, posm_id: int) -> Optional[PosmStockResponse]:
        """POSM stok bilgisini getir"""
        posm = self.db.query(Posm).filter(Posm.id == posm_id).first()
        if not posm:
            return None
        
        return PosmStockResponse(
            hazirAdet=posm.ready_count,
            tamirBekleyen=posm.repair_pending_count
        )

    def create_posm(self, posm_data: PosmCreateRequest) -> PosmResponse:
        """Yeni POSM oluştur"""
        posm = Posm(
            name=posm_data.name,
            depot_id=posm_data.depot_id,
            ready_count=posm_data.ready_count,
            repair_pending_count=posm_data.repair_pending_count
        )
        self.db.add(posm)
        self.db.commit()
        self.db.refresh(posm)
        
        return PosmResponse(
            id=posm.id,
            name=posm.name,
            depot_id=posm.depot_id,
            ready_count=posm.ready_count,
            repair_pending_count=posm.repair_pending_count
        )

    def update_posm(self, posm_id: int, update_data: PosmUpdateRequest) -> Optional[PosmResponse]:
        """POSM güncelle"""
        posm = self.db.query(Posm).filter(Posm.id == posm_id).first()
        if not posm:
            return None
        
        if update_data.name is not None:
            posm.name = update_data.name
        if update_data.ready_count is not None:
            posm.ready_count = update_data.ready_count
        if update_data.repair_pending_count is not None:
            posm.repair_pending_count = update_data.repair_pending_count
        
        self.db.commit()
        self.db.refresh(posm)
        
        return PosmResponse(
            id=posm.id,
            name=posm.name,
            depot_id=posm.depot_id,
            ready_count=posm.ready_count,
            repair_pending_count=posm.repair_pending_count
        )

    def delete_posm(self, posm_id: int) -> bool:
        """POSM sil"""
        posm = self.db.query(Posm).filter(Posm.id == posm_id).first()
        if not posm:
            return False
        
        self.db.delete(posm)
        self.db.commit()
        return True

    def transfer_posm(self, transfer_data: PosmTransferRequest, transferred_by: int) -> PosmTransferResponse:
        """POSM transfer et (depolar arası)"""
        # Kaynak depodaki POSM'i bul
        from_posm = self.db.query(Posm).filter(
            Posm.id == transfer_data.posm_id,
            Posm.depot_id == transfer_data.from_depot_id
        ).first()
        
        if not from_posm:
            raise ValueError("Kaynak depoda POSM bulunamadı")
        
        # Stok kontrolü
        if transfer_data.transfer_type == "ready":
            if from_posm.ready_count < transfer_data.quantity:
                raise ValueError(f"Yetersiz hazır stok. Mevcut: {from_posm.ready_count}, İstenen: {transfer_data.quantity}")
            from_posm.ready_count -= transfer_data.quantity
        elif transfer_data.transfer_type == "repair_pending":
            if from_posm.repair_pending_count < transfer_data.quantity:
                raise ValueError(f"Yetersiz tamir bekleyen stok. Mevcut: {from_posm.repair_pending_count}, İstenen: {transfer_data.quantity}")
            from_posm.repair_pending_count -= transfer_data.quantity
        else:
            raise ValueError("Geçersiz transfer tipi. 'ready' veya 'repair_pending' olmalı")
        
        # Hedef depoda aynı isimde POSM var mı kontrol et
        to_posm = self.db.query(Posm).filter(
            Posm.name == from_posm.name,
            Posm.depot_id == transfer_data.to_depot_id
        ).first()
        
        if to_posm:
            # Mevcut POSM'e ekle
            if transfer_data.transfer_type == "ready":
                to_posm.ready_count += transfer_data.quantity
            else:
                to_posm.repair_pending_count += transfer_data.quantity
        else:
            # Yeni POSM oluştur
            to_posm = Posm(
                name=from_posm.name,
                depot_id=transfer_data.to_depot_id,
                ready_count=transfer_data.quantity if transfer_data.transfer_type == "ready" else 0,
                repair_pending_count=transfer_data.quantity if transfer_data.transfer_type == "repair_pending" else 0
            )
            self.db.add(to_posm)
        
        # Transfer kaydı oluştur
        transfer = PosmTransfer(
            posm_id=transfer_data.posm_id,
            from_depot_id=transfer_data.from_depot_id,
            to_depot_id=transfer_data.to_depot_id,
            quantity=transfer_data.quantity,
            transfer_type=transfer_data.transfer_type,
            notes=transfer_data.notes,
            transferred_by=transferred_by
        )
        self.db.add(transfer)
        self.db.commit()
        self.db.refresh(transfer)
        
        return PosmTransferResponse(
            id=transfer.id,
            posm_id=transfer.posm_id,
            from_depot_id=transfer.from_depot_id,
            to_depot_id=transfer.to_depot_id,
            quantity=transfer.quantity,
            transfer_type=transfer.transfer_type,
            notes=transfer.notes,
            transferred_by=transfer.transferred_by,
            created_at=transfer.created_at.isoformat()
        )

    def get_transfers(self, depot_id: Optional[int] = None) -> List[PosmTransferResponse]:
        """Transfer geçmişini getir"""
        query = self.db.query(PosmTransfer)
        
        if depot_id:
            query = query.filter(
                (PosmTransfer.from_depot_id == depot_id) | 
                (PosmTransfer.to_depot_id == depot_id)
            )
        
        transfers = query.order_by(PosmTransfer.created_at.desc()).all()
        return [PosmTransferResponse(
            id=t.id,
            posm_id=t.posm_id,
            from_depot_id=t.from_depot_id,
            to_depot_id=t.to_depot_id,
            quantity=t.quantity,
            transfer_type=t.transfer_type,
            notes=t.notes,
            transferred_by=t.transferred_by,
            created_at=t.created_at.isoformat()
        ) for t in transfers]
