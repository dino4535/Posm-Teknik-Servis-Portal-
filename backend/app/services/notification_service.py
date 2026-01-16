import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.request import Request
from app.core.config import settings
import os
import ssl


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """Email gönder (opsiyonel - SMTP ayarları yoksa log'a yazar)"""
        # SMTP ayarları yoksa sadece log'a yaz
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from_env = os.getenv("SMTP_FROM", smtp_user)
        # SMTP_FROM email adresi olmalı, domain değil
        # Eğer SMTP_FROM bir email değilse (domain ise), SMTP_USER'ı kullan
        if smtp_from_env and "@" in smtp_from_env:
            smtp_from = smtp_from_env
        else:
            smtp_from = smtp_user if smtp_user else smtp_from_env
        
        if not smtp_host or not smtp_user or not smtp_password:
            # SMTP ayarları yoksa sadece log
            print(f"📧 [EMAIL] To: {to_email}, Subject: {subject}")
            print(f"   {body_text or body_html[:200]}")
            return True
        
        try:
            message = MIMEMultipart("alternative")
            message["From"] = smtp_from
            message["To"] = to_email
            message["Subject"] = subject
            
            if body_text:
                message.attach(MIMEText(body_text, "plain"))
            message.attach(MIMEText(body_html, "html"))
            
            # SSL context oluştur (sertifika doğrulaması kapalı)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Port 587 için STARTTLS kullan
            # Port 465 için SSL/TLS kullan
            if smtp_port == 587:
                # STARTTLS kullan, sertifika doğrulaması kapalı
                await aiosmtplib.send(
                    message,
                    hostname=smtp_host,
                    port=smtp_port,
                    username=smtp_user,
                    password=smtp_password,
                    use_tls=False,
                    start_tls=True,
                    tls_context=ssl_context  # SSL context ile sertifika doğrulaması kapalı
                )
            elif smtp_port == 465:
                # SSL/TLS kullan, sertifika doğrulaması kapalı
                await aiosmtplib.send(
                    message,
                    hostname=smtp_host,
                    port=smtp_port,
                    username=smtp_user,
                    password=smtp_password,
                    use_tls=True,
                    start_tls=False,
                    tls_context=ssl_context  # SSL context ile sertifika doğrulaması kapalı
                )
            else:
                # Varsayılan: STARTTLS dene, sertifika doğrulaması kapalı
                await aiosmtplib.send(
                    message,
                    hostname=smtp_host,
                    port=smtp_port,
                    username=smtp_user,
                    password=smtp_password,
                    use_tls=False,
                    start_tls=True,
                    tls_context=ssl_context  # SSL context ile sertifika doğrulaması kapalı
                )
            print(f"✅ Email başarıyla gönderildi: {to_email}")
            return True
        except Exception as e:
            print(f"❌ Email gönderme hatası: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def notify_request_planned(
        self,
        request: Request,
        planned_date: str,
        updated_by_user: User
    ):
        """İş planlandığında kullanıcıya bildirim gönder"""
        user = self.db.query(User).filter(User.id == request.user_id).first()
        if not user or not user.email:
            return
        
        subject = f"İş Planlama Bildirimi - Talep No: {request.id}"
        body_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #2d3748; background-color: #f7fafc; margin: 0; padding: 0;">
            <div style="max-width: 650px; margin: 30px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%); padding: 30px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 600;">İş Planlama Bildirimi</h1>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <p style="font-size: 16px; color: #2d3748; margin-bottom: 20px;">Sayın {user.name},</p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-bottom: 25px;">
                        Oluşturduğunuz teknik servis talebi planlama sürecine alınmıştır. Aşağıda talebinize ilişkin detaylı bilgiler yer almaktadır.
                    </p>
                    
                    <div style="background: #f7fafc; border-left: 4px solid #4299e1; padding: 20px; border-radius: 6px; margin: 25px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748; width: 140px;">Talep Numarası:</td>
                                <td style="padding: 8px 0; color: #4a5568;">#{request.id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Bayi Bilgisi:</td>
                                <td style="padding: 8px 0; color: #4a5568;">{request.dealer.name} ({request.dealer.code})</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">İş Tipi:</td>
                                <td style="padding: 8px 0; color: #4a5568;">{request.job_type}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Planlanan Tarih:</td>
                                <td style="padding: 8px 0; color: #4299e1; font-weight: 600;">{planned_date}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Planlayan Personel:</td>
                                <td style="padding: 8px 0; color: #4a5568;">{updated_by_user.name}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background: #edf2f7; padding: 15px; border-radius: 6px; margin: 25px 0;">
                        <p style="margin: 0; font-size: 14px; color: #2d3748; font-weight: 600;">
                            📅 İşin gerçekleştirilmesi planlanan tarih: <span style="color: #4299e1;">{planned_date}</span>
                        </p>
                    </div>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 25px;">
                        Planlanan tarihte işinizin gerçekleştirilmesi için gerekli hazırlıklar yapılmaktadır. Herhangi bir değişiklik olması durumunda size bilgi verilecektir.
                    </p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 20px;">
                        Sorularınız için lütfen bizimle iletişime geçmekten çekinmeyiniz.
                    </p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 30px;">
                        Saygılarımızla,<br>
                        <strong>Teknik Servis Yönetim Sistemi</strong>
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background: #edf2f7; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0; font-size: 12px; color: #718096;">
                        Bu e-posta otomatik olarak oluşturulmuştur. Lütfen bu e-postaya yanıt vermeyiniz.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
İŞ PLANLAMA BİLDİRİMİ

Sayın {user.name},

Oluşturduğunuz teknik servis talebi planlama sürecine alınmıştır. Aşağıda talebinize ilişkin detaylı bilgiler yer almaktadır.

TALEP DETAYLARI:
----------------
Talep Numarası: #{request.id}
Bayi Bilgisi: {request.dealer.name} ({request.dealer.code})
İş Tipi: {request.job_type}
Planlanan Tarih: {planned_date}
Planlayan Personel: {updated_by_user.name}

Planlanan tarihte işinizin gerçekleştirilmesi için gerekli hazırlıklar yapılmaktadır. Herhangi bir değişiklik olması durumunda size bilgi verilecektir.

Sorularınız için lütfen bizimle iletişime geçmekten çekinmeyiniz.

Saygılarımızla,
Teknik Servis Yönetim Sistemi

---
Bu e-posta otomatik olarak oluşturulmuştur. Lütfen bu e-postaya yanıt vermeyiniz.
        """
        
        await self.send_email(user.email, subject, body_html, body_text)
    
    async def notify_request_completed(
        self,
        request: Request,
        completed_date: str,
        completed_by_user: User
    ):
        """İş tamamlandığında kullanıcıya bildirim gönder"""
        user = self.db.query(User).filter(User.id == request.user_id).first()
        if not user or not user.email:
            return
        
        subject = f"İş Tamamlanma Bildirimi - Talep No: {request.id}"
        body_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #2d3748; background-color: #f7fafc; margin: 0; padding: 0;">
            <div style="max-width: 650px; margin: 30px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 600;">İş Tamamlanma Bildirimi</h1>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <p style="font-size: 16px; color: #2d3748; margin-bottom: 20px;">Sayın {user.name},</p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-bottom: 25px;">
                        Oluşturduğunuz teknik servis talebi başarıyla tamamlanmıştır. Aşağıda işlem detayları yer almaktadır.
                    </p>
                    
                    <div style="background: #f7fafc; border-left: 4px solid #10b981; padding: 20px; border-radius: 6px; margin: 25px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748; width: 140px;">Talep Numarası:</td>
                                <td style="padding: 8px 0; color: #4a5568;">#{request.id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Bayi Bilgisi:</td>
                                <td style="padding: 8px 0; color: #4a5568;">{request.dealer.name} ({request.dealer.code})</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Yapılan İş:</td>
                                <td style="padding: 8px 0; color: #4a5568;">{request.job_type}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Tamamlanma Tarihi:</td>
                                <td style="padding: 8px 0; color: #10b981; font-weight: 600;">{completed_date}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Görevli Personel:</td>
                                <td style="padding: 8px 0; color: #4a5568;">{completed_by_user.name}</td>
                            </tr>
                            {f'<tr><td style="padding: 8px 0; font-weight: 600; color: #2d3748; vertical-align: top;">Yapılan İşlemler:</td><td style="padding: 8px 0; color: #4a5568;">{request.job_done_desc}</td></tr>' if request.job_done_desc else ''}
                        </table>
                    </div>
                    
                    <div style="background: #d1fae5; padding: 15px; border-radius: 6px; margin: 25px 0; border-left: 4px solid #10b981;">
                        <p style="margin: 0; font-size: 14px; color: #065f46; font-weight: 600;">
                            ✅ İşleminiz başarıyla tamamlanmıştır.
                        </p>
                    </div>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 25px;">
                        İşleminizle ilgili herhangi bir sorunuz veya görüşünüz bulunması durumunda, lütfen bizimle iletişime geçmekten çekinmeyiniz.
                    </p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 20px;">
                        Bize güvendiğiniz için teşekkür ederiz.
                    </p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 30px;">
                        Saygılarımızla,<br>
                        <strong>Teknik Servis Yönetim Sistemi</strong>
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background: #edf2f7; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0; font-size: 12px; color: #718096;">
                        Bu e-posta otomatik olarak oluşturulmuştur. Lütfen bu e-postaya yanıt vermeyiniz.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
İŞ TAMAMLANMA BİLDİRİMİ

Sayın {user.name},

Oluşturduğunuz teknik servis talebi başarıyla tamamlanmıştır. Aşağıda işlem detayları yer almaktadır.

İŞLEM DETAYLARI:
----------------
Talep Numarası: #{request.id}
Bayi Bilgisi: {request.dealer.name} ({request.dealer.code})
Yapılan İş: {request.job_type}
Tamamlanma Tarihi: {completed_date}
Görevli Personel: {completed_by_user.name}
{f'Yapılan İşlemler: {request.job_done_desc}' if request.job_done_desc else ''}

İşleminizle ilgili herhangi bir sorunuz veya görüşünüz bulunması durumunda, lütfen bizimle iletişime geçmekten çekinmeyiniz.

Bize güvendiğiniz için teşekkür ederiz.

Saygılarımızla,
Teknik Servis Yönetim Sistemi

---
Bu e-posta otomatik olarak oluşturulmuştur. Lütfen bu e-postaya yanıt vermeyiniz.
        """
        
        await self.send_email(user.email, subject, body_html, body_text)
    
    async def notify_request_updated(
        self,
        request: Request,
        updated_by_user: User,
        changes: dict
    ):
        """Talep güncellendiğinde kullanıcıya bildirim gönder"""
        user = self.db.query(User).filter(User.id == request.user_id).first()
        if not user or not user.email:
            return
        
        changes_text = []
        if "status" in changes:
            changes_text.append(f"Durum: {changes['status']}")
        if "planned_date" in changes:
            changes_text.append(f"Planlanan Tarih: {changes['planned_date']}")
        if "job_done_desc" in changes:
            changes_text.append("Yapılan İşler açıklaması güncellendi")
        
        if not changes_text:
            return
        
        subject = f"Talep Güncelleme Bildirimi - Talep No: {request.id}"
        body_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #2d3748; background-color: #f7fafc; margin: 0; padding: 0;">
            <div style="max-width: 650px; margin: 30px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 600;">Talep Güncelleme Bildirimi</h1>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <p style="font-size: 16px; color: #2d3748; margin-bottom: 20px;">Sayın {user.name},</p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-bottom: 25px;">
                        Oluşturduğunuz teknik servis talebinde güncelleme yapılmıştır. Aşağıda güncellenen bilgiler yer almaktadır.
                    </p>
                    
                    <div style="background: #f7fafc; border-left: 4px solid #667eea; padding: 20px; border-radius: 6px; margin: 25px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748; width: 140px;">Talep Numarası:</td>
                                <td style="padding: 8px 0; color: #4a5568;">#{request.id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Bayi Bilgisi:</td>
                                <td style="padding: 8px 0; color: #4a5568;">{request.dealer.name} ({request.dealer.code})</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748; vertical-align: top;">Güncellemeler:</td>
                                <td style="padding: 8px 0; color: #4a5568;">
                                    <ul style="margin: 0; padding-left: 20px;">
                                        {''.join([f'<li style="margin-bottom: 5px;">{change}</li>' for change in changes_text])}
                                    </ul>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Güncelleyen Personel:</td>
                                <td style="padding: 8px 0; color: #4a5568;">{updated_by_user.name}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 25px;">
                        Talebinizle ilgili güncel bilgileri sistem üzerinden takip edebilirsiniz. Herhangi bir sorunuz bulunması durumunda, lütfen bizimle iletişime geçmekten çekinmeyiniz.
                    </p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 30px;">
                        Saygılarımızla,<br>
                        <strong>Teknik Servis Yönetim Sistemi</strong>
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background: #edf2f7; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0; font-size: 12px; color: #718096;">
                        Bu e-posta otomatik olarak oluşturulmuştur. Lütfen bu e-postaya yanıt vermeyiniz.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
TALEP GÜNCELLEME BİLDİRİMİ

Sayın {user.name},

Oluşturduğunuz teknik servis talebinde güncelleme yapılmıştır. Aşağıda güncellenen bilgiler yer almaktadır.

TALEP DETAYLARI:
----------------
Talep Numarası: #{request.id}
Bayi Bilgisi: {request.dealer.name} ({request.dealer.code})

Güncellemeler:
{chr(10).join([f'  • {change}' for change in changes_text])}

Güncelleyen Personel: {updated_by_user.name}

Talebinizle ilgili güncel bilgileri sistem üzerinden takip edebilirsiniz. Herhangi bir sorunuz bulunması durumunda, lütfen bizimle iletişime geçmekten çekinmeyiniz.

Saygılarımızla,
Teknik Servis Yönetim Sistemi

---
Bu e-posta otomatik olarak oluşturulmuştur. Lütfen bu e-postaya yanıt vermeyiniz.
        """
        
        await self.send_email(user.email, subject, body_html, body_text)
    
    async def notify_request_created(
        self,
        request: Request,
        created_by_user: User
    ):
        """Talep oluşturulduğunda kullanıcıya bildirim gönder"""
        if not created_by_user.email:
            return
        
        subject = f"Talep Oluşturma Onayı - Talep No: {request.id}"
        body_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #2d3748; background-color: #f7fafc; margin: 0; padding: 0;">
            <div style="max-width: 650px; margin: 30px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%); padding: 30px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 600;">Talep Oluşturma Onayı</h1>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <p style="font-size: 16px; color: #2d3748; margin-bottom: 20px;">Sayın {created_by_user.name},</p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-bottom: 25px;">
                        Teknik servis talebiniz başarıyla oluşturulmuştur. Talebiniz ilgili birimlere iletilmiş olup, en kısa sürede değerlendirilecektir.
                    </p>
                    
                    <div style="background: #f7fafc; border-left: 4px solid #4299e1; padding: 20px; border-radius: 6px; margin: 25px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748; width: 140px;">Talep Numarası:</td>
                                <td style="padding: 8px 0; color: #4a5568;">#{request.id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Bayi Bilgisi:</td>
                                <td style="padding: 8px 0; color: #4a5568;">{request.dealer.name} ({request.dealer.code})</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Yapılacak İş:</td>
                                <td style="padding: 8px 0; color: #4a5568;">{request.job_type}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">İstenen Tarih:</td>
                                <td style="padding: 8px 0; color: #4a5568;">{request.requested_date.strftime('%d.%m.%Y') if request.requested_date else '-'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Durum:</td>
                                <td style="padding: 8px 0; color: #4299e1; font-weight: 600;">{request.status}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background: #dbeafe; padding: 15px; border-radius: 6px; margin: 25px 0; border-left: 4px solid #4299e1;">
                        <p style="margin: 0; font-size: 14px; color: #1e40af; font-weight: 600;">
                            ℹ️ Talebiniz teknik sorumlulara iletilmiştir ve en kısa sürede planlama sürecine alınacaktır.
                        </p>
                    </div>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 25px;">
                        Talebinizin durumunu sistem üzerinden takip edebilirsiniz. Planlama süreci tamamlandığında size bilgilendirme yapılacaktır.
                    </p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 20px;">
                        Bize güvendiğiniz için teşekkür ederiz.
                    </p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 30px;">
                        Saygılarımızla,<br>
                        <strong>Teknik Servis Yönetim Sistemi</strong>
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background: #edf2f7; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0; font-size: 12px; color: #718096;">
                        Bu e-posta otomatik olarak oluşturulmuştur. Lütfen bu e-postaya yanıt vermeyiniz.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
TALEP OLUŞTURMA ONAYI

Sayın {created_by_user.name},

Teknik servis talebiniz başarıyla oluşturulmuştur. Talebiniz ilgili birimlere iletilmiş olup, en kısa sürede değerlendirilecektir.

TALEP DETAYLARI:
----------------
Talep Numarası: #{request.id}
Bayi Bilgisi: {request.dealer.name} ({request.dealer.code})
Yapılacak İş: {request.job_type}
İstenen Tarih: {request.requested_date.strftime('%d.%m.%Y') if request.requested_date else '-'}
Durum: {request.status}

Talebiniz teknik sorumlulara iletilmiştir ve en kısa sürede planlama sürecine alınacaktır.

Talebinizin durumunu sistem üzerinden takip edebilirsiniz. Planlama süreci tamamlandığında size bilgilendirme yapılacaktır.

Bize güvendiğiniz için teşekkür ederiz.

Saygılarımızla,
Teknik Servis Yönetim Sistemi

---
Bu e-posta otomatik olarak oluşturulmuştur. Lütfen bu e-postaya yanıt vermeyiniz.
        """
        
        await self.send_email(created_by_user.email, subject, body_html, body_text)
    
    async def notify_new_request_to_tech(
        self,
        request: Request,
        tech_user: User,
        created_by_user: User
    ):
        """Yeni talep teknik sorumluya bildirimi"""
        if not tech_user.email:
            return
        
        depot_name = request.depot.name if request.depot else "Bilinmeyen Depo"
        
        subject = f"Yeni Talep Bildirimi - Talep No: {request.id} - {depot_name}"
        body_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #2d3748; background-color: #f7fafc; margin: 0; padding: 0;">
            <div style="max-width: 650px; margin: 30px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 30px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 600;">Yeni Talep Bildirimi</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{depot_name} Deposu</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <p style="font-size: 16px; color: #2d3748; margin-bottom: 20px;">Sayın {tech_user.name},</p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-bottom: 25px;">
                        <strong>{depot_name}</strong> deposu için yeni bir teknik servis talebi oluşturulmuştur. Aşağıda talep detayları yer almaktadır.
                    </p>
                    
                    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; border-radius: 6px; margin: 25px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748; width: 140px;">Talep Numarası:</td>
                                <td style="padding: 8px 0; color: #92400e; font-weight: 600;">#{request.id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Bayi Bilgisi:</td>
                                <td style="padding: 8px 0; color: #92400e;">{request.dealer.name} ({request.dealer.code})</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Yapılacak İş:</td>
                                <td style="padding: 8px 0; color: #92400e;">{request.job_type}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748; vertical-align: top;">İş Detayı:</td>
                                <td style="padding: 8px 0; color: #92400e;">{request.job_detail or 'Detay belirtilmemiş'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">İstenen Tarih:</td>
                                <td style="padding: 8px 0; color: #92400e;">{request.requested_date.strftime('%d.%m.%Y') if request.requested_date else '-'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Talep Eden:</td>
                                <td style="padding: 8px 0; color: #92400e;">{created_by_user.name} ({created_by_user.email})</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #2d3748;">Durum:</td>
                                <td style="padding: 8px 0; color: #92400e; font-weight: 600;">{request.status}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background: #fef3c7; padding: 15px; border-radius: 6px; margin: 25px 0; border-left: 4px solid #f59e0b;">
                        <p style="margin: 0; font-size: 14px; color: #92400e; font-weight: 600;">
                            ⚠️ Lütfen iş planı sayfasından bu talebi planlama sürecine alınız.
                        </p>
                    </div>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 25px;">
                        Talebin planlanması için gerekli işlemleri en kısa sürede gerçekleştirmeniz önemle rica olunur.
                    </p>
                    
                    <p style="font-size: 15px; color: #4a5568; margin-top: 30px;">
                        Saygılarımızla,<br>
                        <strong>Teknik Servis Yönetim Sistemi</strong>
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background: #edf2f7; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0; font-size: 12px; color: #718096;">
                        Bu e-posta otomatik olarak oluşturulmuştur. Lütfen bu e-postaya yanıt vermeyiniz.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
YENİ TALEP BİLDİRİMİ

Sayın {tech_user.name},

{depot_name} deposu için yeni bir teknik servis talebi oluşturulmuştur. Aşağıda talep detayları yer almaktadır.

TALEP DETAYLARI:
----------------
Talep Numarası: #{request.id}
Bayi Bilgisi: {request.dealer.name} ({request.dealer.code})
Yapılacak İş: {request.job_type}
İş Detayı: {request.job_detail or 'Detay belirtilmemiş'}
İstenen Tarih: {request.requested_date.strftime('%d.%m.%Y') if request.requested_date else '-'}
Talep Eden: {created_by_user.name} ({created_by_user.email})
Durum: {request.status}

Lütfen iş planı sayfasından bu talebi planlama sürecine alınız.

Talebin planlanması için gerekli işlemleri en kısa sürede gerçekleştirmeniz önemle rica olunur.

Saygılarımızla,
Teknik Servis Yönetim Sistemi

---
Bu e-posta otomatik olarak oluşturulmuştur. Lütfen bu e-postaya yanıt vermeyiniz.
        """
        
        await self.send_email(tech_user.email, subject, body_html, body_text)
