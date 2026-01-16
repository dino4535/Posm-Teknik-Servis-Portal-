from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.notification_service import NotificationService
from app.models.request import Request, RequestStatus
from app.models.user import User
from app.models.depot import Depot
import pandas as pd
import io
import asyncio


def get_completed_requests_last_week(db: Session, depot_ids: list = None):
    """Geçen hafta (Pazar gününden önceki hafta) tamamlanan işleri getir"""
    today = datetime.now().date()
    # Son Pazar gününü bul
    days_since_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_sunday)
    week_start = last_sunday - timedelta(days=6)  # Pazartesi
    week_end = last_sunday  # Pazar
    
    query = db.query(Request).filter(
        Request.status == RequestStatus.TAMAMLANDI.value,
        Request.completed_date >= week_start,
        Request.completed_date <= week_end
    )
    
    if depot_ids:
        query = query.filter(Request.depot_id.in_(depot_ids))
    
    return query.all()


def get_pending_and_planned_requests(db: Session, depot_ids: list = None, status_filter: list = None, job_type_filter: list = None):
    """Bekleyen ve planlanmış işleri getir"""
    query = db.query(Request).filter(
        Request.status.in_([RequestStatus.BEKLEMEDE.value, RequestStatus.TAKVIME_EKLENDI.value])
    )
    
    if depot_ids:
        query = query.filter(Request.depot_id.in_(depot_ids))
    
    if status_filter:
        query = query.filter(Request.status.in_(status_filter))
    
    if job_type_filter:
        query = query.filter(Request.job_type.in_(job_type_filter))
    
    return query.all()


def get_email_template_header():
    """Email template header (logo ve şirket bilgileri)"""
    return """
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px 20px; text-align: center;">
        <div style="max-width: 600px; margin: 0 auto;">
            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600; letter-spacing: 0.5px;">
                Teknik Servis Portalı
            </h1>
            <p style="color: #e0e7ff; margin: 8px 0 0 0; font-size: 14px;">
                Otomatik Rapor Sistemi
            </p>
        </div>
    </div>
    """

def get_email_template_footer():
    """Email template footer (iletişim ve yasal bilgiler)"""
    return f"""
    <div style="background-color: #f7fafc; padding: 30px 20px; margin-top: 40px; border-top: 3px solid #667eea;">
        <div style="max-width: 600px; margin: 0 auto; text-align: center;">
            <p style="color: #4a5568; font-size: 13px; margin: 8px 0; line-height: 1.6;">
                <strong>Teknik Servis Portalı</strong><br>
                Bu e-posta otomatik olarak oluşturulmuştur.
            </p>
            <p style="color: #718096; font-size: 12px; margin: 12px 0 0 0;">
                © {datetime.now().year} Teknik Servis Portalı. Tüm hakları saklıdır.
            </p>
            <p style="color: #a0aec0; font-size: 11px; margin: 8px 0 0 0;">
                Bu e-postayı yanıtlamayın. Sorularınız için sistem yöneticisi ile iletişime geçin.
            </p>
        </div>
    </div>
    """

def generate_weekly_completed_report(requests):
    """Haftalık tamamlanan işler raporu oluştur"""
    header = get_email_template_header()
    footer = get_email_template_footer()
    
    if not requests:
        # Boş rapor için HTML oluştur
        html_content = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f7fafc;
                    color: #2d3748;
                    line-height: 1.6;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .content {{
                    padding: 40px 30px;
                }}
                h2 {{
                    color: #1a202c;
                    font-size: 24px;
                    font-weight: 600;
                    margin: 0 0 24px 0;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 12px;
                }}
                .summary {{
                    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 30px;
                    border-left: 4px solid #667eea;
                }}
                .summary p {{
                    margin: 8px 0;
                    color: #4a5568;
                    font-size: 14px;
                }}
                .summary strong {{
                    color: #2d3748;
                    font-weight: 600;
                }}
                .empty-state {{
                    text-align: center;
                    padding: 40px 20px;
                    color: #718096;
                }}
                .empty-state-icon {{
                    font-size: 48px;
                    margin-bottom: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                {header}
                <div class="content">
                    <h2>Haftalık Tamamlanan İşler Raporu</h2>
                    <div class="summary">
                        <p><strong>Rapor Tarihi:</strong> {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
                        <p><strong>Toplam Tamamlanan İş Sayısı:</strong> 0</p>
                    </div>
                    <div class="empty-state">
                        <div class="empty-state-icon">📊</div>
                        <p style="font-size: 16px; margin: 0;"><strong>Bu hafta tamamlanan iş bulunamadı.</strong></p>
                        <p style="font-size: 14px; margin: 8px 0 0 0;">Seçilen tarih aralığında tamamlanmış iş kaydı bulunmamaktadır.</p>
                    </div>
                </div>
                {footer}
            </div>
        </body>
        </html>
        """
        return html_content
    
    # Manuel HTML tablo oluştur (daha fazla kontrol için)
    html_table_rows = []
    for idx, req in enumerate(requests, 1):
        depot_name = req.depot.name if req.depot else "Belirtilmemiş"
        
        # Durum badge'i
        status_badge = f'<span style="display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; background-color: #d1fae5; color: #065f46;">{req.status}</span>'
        
        # İş tipi ikonu
        job_icon = "🔧" if req.job_type == "Montaj" else "📦" if req.job_type == "Demontaj" else "⚙️"
        
        row_class = "table-row-even" if idx % 2 == 0 else "table-row-odd"
        html_table_rows.append(f"""
            <tr class="{row_class}">
                <td style="font-weight: 600; color: #667eea;">#{req.id}</td>
                <td>{req.request_date.strftime("%d.%m.%Y %H:%M") if req.request_date else "-"}</td>
                <td><strong>{req.completed_date.strftime("%d.%m.%Y") if req.completed_date else "-"}</strong></td>
                <td style="font-family: monospace; font-size: 12px;">{req.dealer.code}</td>
                <td><strong>{req.dealer.name}</strong></td>
                <td><span style="background-color: #e0e7ff; color: #3730a3; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">{depot_name}</span></td>
                <td>{job_icon} {req.job_type}</td>
                <td>{status_badge}</td>
                <td>{req.user.name}</td>
                <td>{req.completed_by_user.name if req.completed_by_user else "<span style='color: #a0aec0;'>-</span>"}</td>
            </tr>
        """)
    
    html_table = f"""
    <div style="overflow-x: auto; margin-top: 20px; -webkit-overflow-scrolling: touch;">
        <table class="report-table" style="width: 100%; min-width: 1000px; border-collapse: separate; border-spacing: 0;">
            <thead style="display: table-header-group;">
                <tr>
                    <th style="width: 60px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">ID</th>
                    <th style="width: 140px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Talep Tarihi</th>
                    <th style="width: 120px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Tamamlanma</th>
                    <th style="width: 100px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Bayi Kodu</th>
                    <th style="width: 150px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Bayi Adı</th>
                    <th style="width: 90px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Depo</th>
                    <th style="width: 100px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">İş Tipi</th>
                    <th style="width: 100px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Durum</th>
                    <th style="width: 120px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Oluşturan</th>
                    <th style="width: 120px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Tamamlayan</th>
                </tr>
            </thead>
            <tbody>
                {''.join(html_table_rows)}
            </tbody>
        </table>
    </div>
    """
    
    header = get_email_template_header()
    footer = get_email_template_footer()
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f7fafc;
                color: #2d3748;
                line-height: 1.6;
            }}
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .content {{
                padding: 40px 30px;
            }}
            h2 {{
                color: #1a202c;
                font-size: 24px;
                font-weight: 600;
                margin: 0 0 24px 0;
                border-bottom: 3px solid #667eea;
                padding-bottom: 12px;
            }}
            .summary {{
                background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 30px;
                border-left: 4px solid #667eea;
            }}
            .summary p {{
                margin: 8px 0;
                color: #4a5568;
                font-size: 14px;
            }}
            .summary strong {{
                color: #2d3748;
                font-weight: 600;
            }}
            .report-table {{
                border-collapse: separate;
                border-spacing: 0;
                width: 100%;
                background-color: #ffffff;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
                border-radius: 12px;
                overflow: hidden;
            }}
            .report-table thead {{
                display: table-header-group !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .report-table th {{
                display: table-cell !important;
                color: #ffffff !important;
                padding: 16px 14px !important;
                text-align: left !important;
                font-weight: 700 !important;
                font-size: 12px !important;
                text-transform: uppercase !important;
                letter-spacing: 0.8px !important;
                border-bottom: 2px solid rgba(255, 255, 255, 0.2) !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            }}
            .report-table th:first-child {{
                border-top-left-radius: 12px;
            }}
            .report-table th:last-child {{
                border-top-right-radius: 12px;
            }}
            .report-table td {{
                padding: 14px;
                font-size: 13px;
                color: #4a5568;
                border-bottom: 1px solid #e2e8f0;
                vertical-align: middle;
            }}
            .report-table tbody tr:last-child td {{
                border-bottom: none;
            }}
            .table-row-odd {{
                background-color: #ffffff;
            }}
            .table-row-even {{
                background-color: #f8f9fa;
            }}
            .report-table tbody tr:hover {{
                background-color: #f0f4ff !important;
                transform: scale(1.01);
                transition: all 0.2s ease;
                box-shadow: 0 2px 4px rgba(102, 126, 234, 0.1);
            }}
            .report-table tbody tr {{
                transition: all 0.2s ease;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            {header}
            <div class="content">
                <h2>Haftalık Tamamlanan İşler Raporu</h2>
                <div class="summary">
                    <p><strong>Rapor Tarihi:</strong> {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
                    <p><strong>Toplam Tamamlanan İş Sayısı:</strong> <span style="color: #667eea; font-size: 16px; font-weight: 700;">{len(requests)}</span></p>
                </div>
                {html_table}
            </div>
            {footer}
        </div>
    </body>
    </html>
    """
    
    return html_content


def generate_pending_requests_report(requests):
    """Bekleyen ve planlanmış işler raporu oluştur"""
    header = get_email_template_header()
    footer = get_email_template_footer()
    
    if not requests:
        # Boş rapor için HTML oluştur
        html_content = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f7fafc;
                    color: #2d3748;
                    line-height: 1.6;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .content {{
                    padding: 40px 30px;
                }}
                h2 {{
                    color: #1a202c;
                    font-size: 24px;
                    font-weight: 600;
                    margin: 0 0 24px 0;
                    border-bottom: 3px solid #fbbf24;
                    padding-bottom: 12px;
                }}
                .summary {{
                    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 30px;
                    border-left: 4px solid #fbbf24;
                }}
                .summary p {{
                    margin: 8px 0;
                    color: #78350f;
                    font-size: 14px;
                }}
                .summary strong {{
                    color: #92400e;
                    font-weight: 600;
                }}
                .empty-state {{
                    text-align: center;
                    padding: 40px 20px;
                    color: #718096;
                }}
                .empty-state-icon {{
                    font-size: 48px;
                    margin-bottom: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                {header}
                <div class="content">
                    <h2>Bekleyen ve Planlanmış İşler Raporu</h2>
                    <div class="summary">
                        <p><strong>Rapor Tarihi:</strong> {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
                        <p><strong>Bekleyen İş Sayısı:</strong> 0</p>
                        <p><strong>Planlanmış İş Sayısı:</strong> 0</p>
                        <p><strong>Toplam:</strong> 0</p>
                    </div>
                    <div class="empty-state">
                        <div class="empty-state-icon">📋</div>
                        <p style="font-size: 16px; margin: 0;"><strong>Bekleyen veya planlanmış iş bulunamadı.</strong></p>
                        <p style="font-size: 14px; margin: 8px 0 0 0;">Seçilen filtreler için uygun iş kaydı bulunmamaktadır.</p>
                    </div>
                </div>
                {footer}
            </div>
        </body>
        </html>
        """
        return html_content
    
    # Manuel HTML tablo oluştur (daha fazla kontrol için)
    html_table_rows = []
    for idx, req in enumerate(requests, 1):
        depot_name = req.depot.name if req.depot else "Belirtilmemiş"
        
        # Durum badge'i
        if req.status == "Beklemede":
            status_badge = '<span style="display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; background-color: #fee2e2; color: #991b1b;">⏳ Beklemede</span>'
        elif req.status == "TakvimeEklendi":
            status_badge = '<span style="display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; background-color: #dbeafe; color: #1e40af;">📅 Planlandı</span>'
        else:
            status_badge = f'<span style="display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; background-color: #f3f4f6; color: #4b5563;">{req.status}</span>'
        
        # Öncelik badge'i
        priority_colors = {
            "Düşük": "#e0e7ff",
            "Orta": "#fef3c7",
            "Yüksek": "#fed7aa",
            "Acil": "#fee2e2"
        }
        priority_text_colors = {
            "Düşük": "#3730a3",
            "Orta": "#92400e",
            "Yüksek": "#9a3412",
            "Acil": "#991b1b"
        }
        priority_icon = {
            "Düşük": "🔵",
            "Orta": "🟡",
            "Yüksek": "🟠",
            "Acil": "🔴"
        }
        priority_bg = priority_colors.get(req.priority, "#f3f4f6")
        priority_text = priority_text_colors.get(req.priority, "#4b5563")
        priority_ic = priority_icon.get(req.priority, "⚪")
        priority_badge = f'<span style="display: inline-block; padding: 4px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; background-color: {priority_bg}; color: {priority_text};">{priority_ic} {req.priority}</span>'
        
        # İş tipi ikonu
        job_icon = "🔧" if req.job_type == "Montaj" else "📦" if req.job_type == "Demontaj" else "⚙️"
        
        # Planlanan tarih
        planned_date = req.planned_date.strftime("%d.%m.%Y") if req.planned_date else '<span style="color: #a0aec0; font-style: italic;">Planlanmadı</span>'
        
        row_class = "table-row-even" if idx % 2 == 0 else "table-row-odd"
        html_table_rows.append(f"""
            <tr class="{row_class}">
                <td style="font-weight: 600; color: #fbbf24;">#{req.id}</td>
                <td>{req.request_date.strftime("%d.%m.%Y %H:%M") if req.request_date else "-"}</td>
                <td>{planned_date}</td>
                <td style="font-family: monospace; font-size: 12px;">{req.dealer.code}</td>
                <td><strong>{req.dealer.name}</strong></td>
                <td><span style="background-color: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">{depot_name}</span></td>
                <td>{job_icon} {req.job_type}</td>
                <td>{priority_badge}</td>
                <td>{status_badge}</td>
                <td>{req.user.name}</td>
            </tr>
        """)
    
    html_table = f"""
    <div style="overflow-x: auto; margin-top: 20px; -webkit-overflow-scrolling: touch;">
        <table class="report-table" style="width: 100%; min-width: 1100px; border-collapse: separate; border-spacing: 0;">
            <thead style="display: table-header-group;">
                <tr>
                    <th style="width: 60px; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">ID</th>
                    <th style="width: 140px; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Talep Tarihi</th>
                    <th style="width: 120px; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Planlanan Tarih</th>
                    <th style="width: 100px; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Bayi Kodu</th>
                    <th style="width: 150px; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Bayi Adı</th>
                    <th style="width: 90px; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Depo</th>
                    <th style="width: 100px; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">İş Tipi</th>
                    <th style="width: 100px; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Öncelik</th>
                    <th style="width: 120px; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Durum</th>
                    <th style="width: 120px; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #ffffff; padding: 16px 14px; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid rgba(255, 255, 255, 0.2);">Oluşturan</th>
                </tr>
            </thead>
            <tbody>
                {''.join(html_table_rows)}
            </tbody>
        </table>
    </div>
    """
    
    pending_count = len([r for r in requests if r.status == RequestStatus.BEKLEMEDE.value])
    planned_count = len([r for r in requests if r.status == RequestStatus.TAKVIME_EKLENDI.value])
    
    header = get_email_template_header()
    footer = get_email_template_footer()
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f7fafc;
                color: #2d3748;
                line-height: 1.6;
            }}
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .content {{
                padding: 40px 30px;
            }}
            h2 {{
                color: #1a202c;
                font-size: 24px;
                font-weight: 600;
                margin: 0 0 24px 0;
                border-bottom: 3px solid #fbbf24;
                padding-bottom: 12px;
            }}
            .summary {{
                background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 30px;
                border-left: 4px solid #fbbf24;
            }}
            .summary p {{
                margin: 8px 0;
                color: #78350f;
                font-size: 14px;
            }}
            .summary strong {{
                color: #92400e;
                font-weight: 600;
            }}
            .summary .stat-value {{
                color: #d97706;
                font-size: 16px;
                font-weight: 700;
            }}
            .report-table {{
                border-collapse: separate;
                border-spacing: 0;
                width: 100%;
                background-color: #ffffff;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
                border-radius: 12px;
                overflow: hidden;
            }}
            .report-table thead {{
                display: table-header-group !important;
                background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            }}
            .report-table th {{
                display: table-cell !important;
                color: #ffffff !important;
                padding: 16px 14px !important;
                text-align: left !important;
                font-weight: 700 !important;
                font-size: 12px !important;
                text-transform: uppercase !important;
                letter-spacing: 0.8px !important;
                border-bottom: 2px solid rgba(255, 255, 255, 0.2) !important;
                background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%) !important;
            }}
            .report-table th:first-child {{
                border-top-left-radius: 12px;
            }}
            .report-table th:last-child {{
                border-top-right-radius: 12px;
            }}
            .report-table td {{
                padding: 14px;
                font-size: 13px;
                color: #4a5568;
                border-bottom: 1px solid #e2e8f0;
                vertical-align: middle;
            }}
            .report-table tbody tr:last-child td {{
                border-bottom: none;
            }}
            .table-row-odd {{
                background-color: #ffffff;
            }}
            .table-row-even {{
                background-color: #fffbeb;
            }}
            .report-table tbody tr:hover {{
                background-color: #fef3c7 !important;
                transform: scale(1.01);
                transition: all 0.2s ease;
                box-shadow: 0 2px 4px rgba(251, 191, 36, 0.2);
            }}
            .report-table tbody tr {{
                transition: all 0.2s ease;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            {header}
            <div class="content">
                <h2>Bekleyen ve Planlanmış İşler Raporu</h2>
                <div class="summary">
                    <p><strong>Rapor Tarihi:</strong> {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
                    <p><strong>Bekleyen İş Sayısı:</strong> <span class="stat-value">{pending_count}</span></p>
                    <p><strong>Planlanmış İş Sayısı:</strong> <span class="stat-value">{planned_count}</span></p>
                    <p><strong>Toplam:</strong> <span class="stat-value">{len(requests)}</span></p>
                </div>
                {html_table}
            </div>
            {footer}
        </div>
    </body>
    </html>
    """
    
    return html_content


async def send_weekly_completed_report():
    """Her Pazar gecesi çalışacak - Geçen hafta tamamlanan işler raporu"""
    db = SessionLocal()
    try:
        requests = get_completed_requests_last_week(db)
        if not requests:
            print("Geçen hafta tamamlanan iş bulunamadı, rapor gönderilmeyecek.")
            return
        
        html_content = generate_weekly_completed_report(requests)
        if not html_content:
            return
        
        # Admin kullanıcılarına gönder
        admin_users = db.query(User).filter(User.role == "admin").all()
        notification_service = NotificationService(db)
        
        for admin in admin_users:
            await notification_service.send_email(
                to_email=admin.email,
                subject=f"Haftalık Tamamlanan İşler Raporu - {datetime.now().strftime('%d.%m.%Y')}",
                body_html=html_content
            )
        
        print(f"Haftalık tamamlanan işler raporu {len(admin_users)} admin kullanıcısına gönderildi.")
    finally:
        db.close()


async def send_pending_requests_report():
    """Her Pazartesi sabah 06:00'da çalışacak - Bekleyen ve planlanmış işler raporu"""
    db = SessionLocal()
    try:
        requests = get_pending_and_planned_requests(db)
        if not requests:
            print("Bekleyen veya planlanmış iş bulunamadı, rapor gönderilmeyecek.")
            return
        
        html_content = generate_pending_requests_report(requests)
        if not html_content:
            return
        
        # Admin kullanıcılarına gönder
        admin_users = db.query(User).filter(User.role == "admin").all()
        notification_service = NotificationService(db)
        
        for admin in admin_users:
            await notification_service.send_email(
                to_email=admin.email,
                subject=f"Bekleyen ve Planlanmış İşler Raporu - {datetime.now().strftime('%d.%m.%Y')}",
                body_html=html_content
            )
        
        print(f"Bekleyen ve planlanmış işler raporu {len(admin_users)} admin kullanıcısına gönderildi.")
    finally:
        db.close()


async def send_custom_report(report_id: int, db: Session = None, skip_active_check: bool = False):
    """Özelleştirilmiş rapor gönder"""
    from app.models.scheduled_report import ScheduledReport
    
    if not db:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        report = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
        if not report:
            print(f"Rapor {report_id} bulunamadı")
            return
        
        if not skip_active_check and not report.is_active:
            print(f"Rapor {report_id} aktif değil")
            return
        
        # Rapor tipine göre veri çek
        if report.report_type == 'weekly_completed':
            requests = get_completed_requests_last_week(db, report.depot_ids)
            html_content = generate_weekly_completed_report(requests)
            subject = f"{report.name} - {datetime.now().strftime('%d.%m.%Y')}"
        elif report.report_type == 'pending_requests':
            requests = get_pending_and_planned_requests(
                db, 
                report.depot_ids, 
                report.status_filter, 
                report.job_type_filter
            )
            html_content = generate_pending_requests_report(requests)
            subject = f"{report.name} - {datetime.now().strftime('%d.%m.%Y')}"
        else:
            # Custom report type - gelecekte genişletilebilir
            print(f"Bilinmeyen rapor tipi: {report.report_type}")
            return
        
        if not html_content:
            print(f"Rapor {report_id} için HTML içeriği oluşturulamadı")
            return
        
        # Alıcı kullanıcıları getir
        recipient_users = db.query(User).filter(User.id.in_(report.recipient_user_ids)).all()
        if not recipient_users:
            print(f"Rapor {report_id} için alıcı kullanıcı bulunamadı")
            return
        
        notification_service = NotificationService(db)
        
        # Her alıcıya gönder
        success_count = 0
        error_count = 0
        for user in recipient_users:
            try:
                result = await notification_service.send_email(
                    to_email=user.email,
                    subject=subject,
                    body_html=html_content
                )
                if result:
                    success_count += 1
                    print(f"✅ Rapor {report_id} gönderildi: {user.email}")
                else:
                    error_count += 1
                    print(f"❌ Rapor {report_id} gönderilemedi: {user.email}")
            except Exception as e:
                error_count += 1
                print(f"❌ Rapor {report_id} gönderme hatası ({user.email}): {str(e)}")
        
        # Son gönderim zamanını güncelle
        if success_count > 0:
            report.last_sent_at = datetime.now()
            db.commit()
            print(f"✅ Rapor {report_id} ({report.name}) {success_count} kullanıcıya başarıyla gönderildi")
        else:
            print(f"⚠️ Rapor {report_id} ({report.name}) hiçbir kullanıcıya gönderilemedi ({error_count} hata)")
    finally:
        if should_close:
            db.close()
