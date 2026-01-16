from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.services.scheduled_report_service import ScheduledReportService
from app.schemas.scheduled_report import ScheduledReportCreate, ScheduledReportUpdate, ScheduledReportResponse
from typing import List

router = APIRouter()


def require_admin(current_user: dict = Depends(AuthService.get_current_user)):
    """Admin yetkisi kontrolü"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    return current_user


@router.post("/", response_model=ScheduledReportResponse)
async def create_scheduled_report(
    report_data: ScheduledReportCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Yeni otomatik rapor oluştur"""
    try:
        report = ScheduledReportService.create_report(db, report_data, current_user["id"])
        
        # Eğer rapor aktifse scheduler'a ekle
        if report.is_active:
            from app.main import scheduler
            from app.services.scheduled_reports import send_custom_report
            from apscheduler.triggers.cron import CronTrigger
            
            try:
                cron_parts = report.cron_expression.split(' ')
                if len(cron_parts) >= 3:
                    day_of_week = int(cron_parts[0])
                    hour = int(cron_parts[1])
                    minute = int(cron_parts[2])
                    
                    async def send_report_wrapper(report_id=report.id):
                        from app.db.session import SessionLocal
                        db = SessionLocal()
                        try:
                            await send_custom_report(report_id, db)
                        finally:
                            db.close()
                    
                    scheduler.add_job(
                        send_report_wrapper,
                        trigger=CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
                        id=f"scheduled_report_{report.id}",
                        replace_existing=True
                    )
                    print(f"✅ Yeni rapor scheduler'a eklendi: {report.name} (ID: {report.id})")
            except Exception as e:
                print(f"⚠️ Rapor scheduler'a eklenemedi {report.id}: {e}")
        
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rapor oluşturma hatası: {str(e)}"
        )


@router.get("/", response_model=List[ScheduledReportResponse])
async def get_scheduled_reports(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Tüm otomatik raporları listele"""
    reports = ScheduledReportService.get_all_reports(db)
    return reports


@router.get("/{report_id}", response_model=ScheduledReportResponse)
async def get_scheduled_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Rapor detayını getir"""
    report = ScheduledReportService.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapor bulunamadı"
        )
    return report


@router.put("/{report_id}", response_model=ScheduledReportResponse)
async def update_scheduled_report(
    report_id: int,
    report_data: ScheduledReportUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Raporu güncelle"""
    report = ScheduledReportService.update_report(db, report_id, report_data)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapor bulunamadı"
        )
    
    # Scheduler'ı güncelle
    from app.main import scheduler
    from app.services.scheduled_reports import send_custom_report
    from apscheduler.triggers.cron import CronTrigger
    
    job_id = f"scheduled_report_{report.id}"
    
    # Eski job'u sil
    try:
        scheduler.remove_job(job_id)
    except:
        pass
    
    # Eğer rapor aktifse yeni job ekle
    if report.is_active:
        try:
            cron_parts = report.cron_expression.split(' ')
            if len(cron_parts) >= 3:
                day_of_week = int(cron_parts[0])
                hour = int(cron_parts[1])
                minute = int(cron_parts[2])
                
                async def send_report_wrapper(report_id=report.id):
                    from app.db.session import SessionLocal
                    db = SessionLocal()
                    try:
                        await send_custom_report(report_id, db)
                    finally:
                        db.close()
                
                scheduler.add_job(
                    send_report_wrapper,
                    trigger=CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
                    id=job_id,
                    replace_existing=True
                )
                print(f"✅ Rapor scheduler'da güncellendi: {report.name} (ID: {report.id})")
        except Exception as e:
            print(f"⚠️ Rapor scheduler'a eklenemedi {report.id}: {e}")
    
    return report


@router.delete("/{report_id}")
async def delete_scheduled_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Raporu sil"""
    success = ScheduledReportService.delete_report(db, report_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapor bulunamadı"
        )
    return {"success": True, "message": "Rapor başarıyla silindi"}


@router.post("/{report_id}/test")
async def test_scheduled_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Raporu test olarak gönder (hemen çalıştır)"""
    from app.services.scheduled_reports import send_custom_report
    
    report = ScheduledReportService.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rapor bulunamadı"
        )
    
    try:
        # Test için aktif kontrolünü atla
        await send_custom_report(report.id, db, skip_active_check=True)
        
        return {"success": True, "message": "Test raporu başarıyla gönderildi"}
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test raporu gönderme hatası: {error_detail}"
        )


@router.get("/users/list")
async def get_users_for_reports(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Rapor gönderimi için kullanılabilir kullanıcıları listele"""
    from app.models.user import User
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
        for user in users
    ]
