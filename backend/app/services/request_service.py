from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.request import Request, JobType, RequestStatus
from app.models.dealer import Dealer
from app.models.user import User
from app.models.territory import Territory
from app.models.posm import Posm
from app.schemas.request import (
    RequestCreate, RequestResponse, RequestDetailResponse,
    RequestUpdate, RequestStatsResponse
)


class RequestService:
    def __init__(self, db: Session):
        self.db = db

    def create_request(self, user_id: int, request_data: RequestCreate) -> Request:
        """Yeni talep oluştur"""
        # Bayi bilgilerini al
        dealer = self.db.query(Dealer).filter(Dealer.id == request_data.dealer_id).first()
        if not dealer:
            raise ValueError("Bayi bulunamadı")
        
        # Territory ID'yi dealer'dan al (eğer request_data'da yoksa)
        territory_id = request_data.territory_id or dealer.territory_id
        
        # Yeni request oluştur
        new_request = Request(
            user_id=user_id,
            dealer_id=dealer.id,
            territory_id=territory_id,
            depot_id=dealer.depot_id,  # Dealer'dan depot_id al
            current_posm=request_data.current_posm,
            job_type=request_data.job_type,
            job_detail=request_data.job_detail,
            requested_date=request_data.requested_date,
            planned_date=request_data.planned_date,
            posm_id=request_data.posm_id,
            status=RequestStatus.BEKLEMEDE.value,
            priority=request_data.priority or "Orta",
            latitude=dealer.latitude,
            longitude=dealer.longitude
        )
        
        self.db.add(new_request)
        self.db.commit()
        self.db.refresh(new_request)
        
        return new_request

    def get_user_requests(self, user_email: str, depot_id: Optional[int] = None, include_depot_requests: bool = False) -> List[RequestResponse]:
        """Kullanıcının taleplerini getir (depot filtresi ile)
        
        Args:
            user_email: Kullanıcı email'i
            depot_id: Filtreleme için depot ID (opsiyonel)
            include_depot_requests: Tech kullanıcılar için kendi depolarındaki tüm talepleri de dahil et
        """
        user = self.db.query(User).filter(User.email == user_email).first()
        if not user:
            return []
        
        # Tech kullanıcılar için: Kendi talepleri + kendi depolarındaki tüm talepler
        user_role = user.role.value if hasattr(user.role, 'value') else user.role
        if include_depot_requests and user_role in ["tech", "admin"]:
            from app.models.user import user_depots
            user_depot_ids = [depot.id for depot in user.depots] if user.depots else []
            if not user_depot_ids and user.depot_id:
                user_depot_ids = [user.depot_id]
            
            if user_depot_ids:
                # Kendi talepleri VEYA kendi depolarındaki talepler
                query = self.db.query(Request).filter(
                    or_(
                        Request.user_id == user.id,
                        Request.depot_id.in_(user_depot_ids)
                    )
                )
            else:
                # Sadece kendi talepleri
                query = self.db.query(Request).filter(Request.user_id == user.id)
        else:
            # Normal kullanıcılar: Sadece kendi talepleri
            query = self.db.query(Request).filter(Request.user_id == user.id)
        
        # Depot filtresi: Eğer parametre olarak depot_id verilmişse
        if depot_id:
            query = query.filter(Request.depot_id == depot_id)
        elif not include_depot_requests and user.depot_id:
            # Normal kullanıcılar için: Kendi depot_id'si varsa filtrele
            query = query.filter(Request.depot_id == user.depot_id)
        
        # Tüm durumları dahil et (tamamlanan dahil) - status filtresi yok
        # request_date: oluşturulma tarihi (DateTime)
        requests = query.order_by(Request.request_date.desc()).all()
        
        return [self._to_response(r) for r in requests]

    def get_all_requests(self, depot_id: Optional[int] = None) -> List[RequestResponse]:
        """Tüm talepleri getir (admin, depot filtresi ile)"""
        query = self.db.query(Request)
        
        if depot_id:
            query = query.filter(Request.depot_id == depot_id)
        
        requests = query.order_by(Request.request_date.desc()).all()
        return [self._to_response(r, include_user=True) for r in requests]

    def get_request_by_id(self, request_id: int) -> Optional[RequestDetailResponse]:
        """Talep detaylarını getir"""
        request = self.db.query(Request).filter(Request.id == request_id).first()
        if not request:
            return None
        
        territory_name = None
        if request.territory:
            territory_name = request.territory.name
        
        posm_name = None
        if request.posm:
            posm_name = request.posm.name
        
        # Fotoğrafları al
        photos = []
        if request.photos:
            photos = [{"url": p.path_or_url, "name": p.file_name} for p in request.photos]
        
        completed_by_name = None
        if request.completed_by_user:
            completed_by_name = request.completed_by_user.name
        
        updated_by_name = None
        if request.updated_by_user:
            updated_by_name = request.updated_by_user.name
        
        # Koordinatları al: Önce request'ten, yoksa dealer'dan
        latitude = request.latitude
        longitude = request.longitude
        if (latitude is None or longitude is None) and request.dealer:
            latitude = request.dealer.latitude
            longitude = request.dealer.longitude
        
        return RequestDetailResponse(
            id=request.id,
            talepTarihi=request.request_date.strftime("%d.%m.%Y %H:%M") if request.request_date else "",
            planlananTarih=request.planned_date.strftime("%d.%m.%Y") if request.planned_date else None,
            tamamlanmaTarihi=request.completed_date.strftime("%d.%m.%Y") if request.completed_date else None,
            territory=territory_name,
            bayiKodu=request.dealer.code,
            bayiAdi=request.dealer.name,
            yapilacakIs=request.job_type,
            yapilacakIsDetay=request.job_detail,
            posmAdi=posm_name,
            durum=request.status,
            oncelik=request.priority,
            yapilanIsler=request.job_done_desc,
            latitude=latitude,
            longitude=longitude,
            photos=photos,
            tamamlayanKullanici=completed_by_name,
            guncelleyenKullanici=updated_by_name
        )

    def update_request(self, request_id: int, update_data: RequestUpdate, updated_by_id: int) -> Optional[Request]:
        """Talep güncelle"""
        request = self.db.query(Request).filter(Request.id == request_id).first()
        if not request:
            return None
        
        from app.models.user import User
        updated_by_user = self.db.query(User).filter(User.id == updated_by_id).first()
        
        changes = {}
        old_status = request.status
        old_planned_date = request.planned_date
        
        if update_data.status is not None:
            request.status = update_data.status
            changes["status"] = update_data.status
            # Eğer durum "Tamamlandı" ise, completed_date ve completed_by'i ayarla
            if update_data.status == RequestStatus.TAMAMLANDI.value:
                if update_data.completed_date:
                    request.completed_date = update_data.completed_date
                else:
                    # Tarih verilmemişse bugünün tarihini kullan
                    from datetime import date
                    request.completed_date = date.today()
                request.completed_by = updated_by_id
            else:
                # Durum "Tamamlandı" değilse, completed_date ve completed_by'i temizle
                request.completed_date = None
                request.completed_by = None
        
        if update_data.planned_date is not None:
            request.planned_date = update_data.planned_date
            changes["planned_date"] = update_data.planned_date.strftime("%d.%m.%Y")
        if update_data.completed_date is not None:
            request.completed_date = update_data.completed_date
        if update_data.job_done_desc is not None:
            request.job_done_desc = update_data.job_done_desc
            changes["job_done_desc"] = True
        if update_data.priority is not None:
            request.priority = update_data.priority
            changes["priority"] = update_data.priority
        
        request.updated_by = updated_by_id
        
        # Not: Bildirimler route seviyesinde BackgroundTasks ile gönderilmeli
        # Burada sadece log yazıyoruz
        pass
        
        # POSM stok güncelleme (Montaj/Demontaj için)
        # Request'in depot_id'si ile POSM'in depot_id'sinin eşleştiğini kontrol et
        if update_data.status == RequestStatus.TAMAMLANDI.value and request.posm:
            # Depot kontrolü: Request'in depot_id'si ile POSM'in depot_id'si eşleşmeli
            if request.depot_id and request.posm.depot_id != request.depot_id:
                # Eğer eşleşmiyorsa, doğru depodaki POSM'i bul
                correct_posm = self.db.query(Posm).filter(
                    Posm.name == request.posm.name,
                    Posm.depot_id == request.depot_id
                ).first()
                if correct_posm:
                    # Doğru depodaki POSM'i kullan
                    if request.job_type == JobType.MONTAJ.value:
                        # Stok kontrolü yap
                        if correct_posm.ready_count <= 0:
                            raise ValueError(f"Yetersiz hazır stok. Mevcut: {correct_posm.ready_count}, İstenen: 1")
                        correct_posm.ready_count -= 1
                    elif request.job_type == JobType.DEMONTAJ.value:
                        correct_posm.repair_pending_count += 1
                else:
                    # Doğru depoda POSM bulunamadı, mevcut POSM'i kullan (backward compatibility)
                    if request.job_type == JobType.MONTAJ.value:
                        # Stok kontrolü yap
                        if request.posm.ready_count <= 0:
                            raise ValueError(f"Yetersiz hazır stok. Mevcut: {request.posm.ready_count}, İstenen: 1")
                        request.posm.ready_count -= 1
                    elif request.job_type == JobType.DEMONTAJ.value:
                        request.posm.repair_pending_count += 1
            else:
                # Normal durum: Depot'lar eşleşiyor veya depot_id yok
                if request.job_type == JobType.MONTAJ.value:
                    # Hazır stoktan düş - stok kontrolü yap
                    if request.posm.ready_count <= 0:
                        raise ValueError(f"Yetersiz hazır stok. Mevcut: {request.posm.ready_count}, İstenen: 1")
                    request.posm.ready_count -= 1
                elif request.job_type == JobType.DEMONTAJ.value:
                    # Tamir bekleyene ekle
                    request.posm.repair_pending_count += 1
        
        self.db.commit()
        self.db.refresh(request)
        
        return request

    def get_request_stats(self, user_email: Optional[str] = None, depot_id: Optional[int] = None) -> RequestStatsResponse:
        """Talep istatistiklerini getir (depot filtresi ile)"""
        query = self.db.query(Request)
        
        # Kullanıcıya özel ise filtrele
        if user_email:
            user = self.db.query(User).filter(User.email == user_email).first()
            if user:
                query = query.filter(Request.user_id == user.id)
                # Kullanıcının depot_id'si varsa filtrele
                if user.depot_id and not depot_id:
                    depot_id = user.depot_id
        
        # Depot filtresi
        if depot_id:
            query = query.filter(Request.depot_id == depot_id)
        
        requests = query.all()
        
        counts = {"open": 0, "completed": 0, "pending": 0}
        
        for req in requests:
            if req.status == RequestStatus.TAMAMLANDI.value:
                counts["completed"] += 1
            elif req.status == RequestStatus.BEKLEMEDE.value:
                counts["pending"] += 1
            else:
                counts["open"] += 1
        
        return RequestStatsResponse(**counts)

    def _to_response(self, request: Request, include_user: bool = False) -> RequestResponse:
        """Request model'ini Response'a çevir"""
        territory_name = None
        if request.territory:
            territory_name = request.territory.name
        
        posm_name = None
        if request.posm:
            posm_name = request.posm.name
        
        response = RequestResponse(
            id=request.id,
            territory=territory_name,
            bayiKodu=request.dealer.code,
            bayiAdi=request.dealer.name,
            mevcutPosm=request.current_posm,
            yapilacakIs=request.job_type,
            talepTarihi=request.request_date.strftime("%d.%m.%Y %H:%M") if request.request_date else "",
            istenentarih=request.requested_date.strftime("%d.%m.%Y") if request.requested_date else "",
            posmAdi=posm_name,
            planlananTarih=request.planned_date.strftime("%d.%m.%Y") if request.planned_date else None,
            yapilanIsler=request.job_done_desc,
            durum=request.status,
            oncelik=request.priority
        )
        
        if include_user:
            response.kullanici = request.user.name
            response.email = request.user.email
        
        return response
