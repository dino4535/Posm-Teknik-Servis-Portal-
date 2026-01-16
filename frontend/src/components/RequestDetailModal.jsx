import { useState, useEffect } from 'react'
import api from '../utils/api'
import '../styles/RequestDetailModal.css'

function RequestDetailModal({ requestId, onClose, onUpdate }) {
  const [request, setRequest] = useState(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [uploadingPhotos, setUploadingPhotos] = useState(false)
  const [newPhotos, setNewPhotos] = useState([])
  const [photoPreview, setPhotoPreview] = useState([])
  const [updateData, setUpdateData] = useState({
    status: '',
    planned_date: '',
    completed_date: '',
    job_done_desc: '',
    priority: ''
  })

  useEffect(() => {
    if (requestId) {
      loadRequestDetails()
    }
  }, [requestId])

  const loadRequestDetails = async () => {
    try {
      const response = await api.get(`/requests/${requestId}`)
      setRequest(response.data)
      setUpdateData({
        status: response.data.durum,
        planned_date: response.data.planlananTarih || '',
        completed_date: response.data.tamamlanmaTarihi || '',
        job_done_desc: response.data.yapilanIsler || '',
        priority: response.data.oncelik || 'Orta'
      })
    } catch (error) {
      console.error('Talep detayları yüklenemedi:', error)
      alert('Talep detayları yüklenemedi')
    } finally {
      setLoading(false)
    }
  }

  const handlePhotoSelect = (e) => {
    const files = Array.from(e.target.files)
    setNewPhotos(prev => [...prev, ...files])
    
    // Önizleme oluştur
    const newPreviews = []
    files.forEach(file => {
      const reader = new FileReader()
      reader.onload = (event) => {
        newPreviews.push({ file, preview: event.target.result })
        if (newPreviews.length === files.length) {
          setPhotoPreview(prev => [...prev, ...newPreviews])
        }
      }
      reader.readAsDataURL(file)
    })
  }

  const handleRemovePhoto = (index) => {
    const newPreviews = photoPreview.filter((_, i) => i !== index)
    const newFiles = newPhotos.filter((_, i) => i !== index)
    setPhotoPreview(newPreviews)
    setNewPhotos(newFiles)
  }

  const handleUploadPhotos = async () => {
    if (newPhotos.length === 0) return

    setUploadingPhotos(true)
    try {
      const formData = new FormData()
      newPhotos.forEach(photo => {
        formData.append('files', photo)
      })

      await api.post(`/photos/requests/${requestId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      setNewPhotos([])
      setPhotoPreview([])
      loadRequestDetails()
      alert('Fotoğraflar başarıyla yüklendi')
    } catch (error) {
      console.error('Fotoğraf yükleme hatası:', error)
      alert(error.response?.data?.detail || 'Fotoğraf yükleme başarısız')
    } finally {
      setUploadingPhotos(false)
    }
  }

  const handleUpdate = async () => {
    setUpdating(true)
    try {
      const updatePayload = {}
      if (updateData.status && updateData.status !== request.durum) {
        updatePayload.status = updateData.status
      }
      if (updateData.planned_date) {
        // DD.MM.YYYY formatından YYYY-MM-DD'ye çevir
        let dateStr = updateData.planned_date
        if (dateStr.includes('.')) {
          const parts = dateStr.split('.')
          if (parts.length === 3) {
            dateStr = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
          }
        }
        updatePayload.planned_date = dateStr
      }
      if (updateData.completed_date) {
        // DD.MM.YYYY formatından YYYY-MM-DD'ye çevir
        let dateStr = updateData.completed_date
        if (dateStr.includes('.')) {
          const parts = dateStr.split('.')
          if (parts.length === 3) {
            dateStr = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
          }
        }
        updatePayload.completed_date = dateStr
      }
      if (updateData.job_done_desc !== request.yapilanIsler) {
        updatePayload.job_done_desc = updateData.job_done_desc
      }
      if (updateData.priority && updateData.priority !== request.oncelik) {
        updatePayload.priority = updateData.priority
      }

      // Önce fotoğrafları yükle (varsa)
      if (newPhotos.length > 0) {
        await handleUploadPhotos()
      }

      // Sonra talep güncellemesini yap
      if (Object.keys(updatePayload).length > 0) {
        await api.patch(`/requests/${requestId}`, updatePayload)
        alert('Talep başarıyla güncellendi')
        if (onUpdate) onUpdate()
        loadRequestDetails()
      } else if (newPhotos.length > 0) {
        // Sadece fotoğraf yükleme varsa
        loadRequestDetails()
      }
    } catch (error) {
      console.error('Güncelleme hatası:', error)
      alert(error.response?.data?.detail || 'Güncelleme başarısız')
    } finally {
      setUpdating(false)
    }
  }

  if (!requestId) return null

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="loading-container">Yükleniyor...</div>
        </div>
      </div>
    )
  }

  if (!request) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="error-message">Talep bulunamadı</div>
          <button onClick={onClose} className="close-btn">Kapat</button>
        </div>
      </div>
    )
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Talep Detayları</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="detail-section">
            <h3>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
              Genel Bilgiler
            </h3>
            <div className="detail-grid">
              <div className="detail-item">
                <label>Talep Tarihi:</label>
                <span>{request.talepTarihi}</span>
              </div>
              <div className="detail-item">
                <label>Durum:</label>
                <span className={`status-badge status-${request.durum.toLowerCase().replace(' ', '-')}`}>
                  {request.durum}
                </span>
              </div>
              <div className="detail-item">
                <label>Öncelik:</label>
                <span className={`priority-badge priority-${request.oncelik?.toLowerCase() || 'orta'}`}>
                  {request.oncelik || 'Orta'}
                </span>
              </div>
              <div className="detail-item">
                <label>Bayi Kodu:</label>
                <span>{request.bayiKodu}</span>
              </div>
              <div className="detail-item">
                <label>Bayi Adı:</label>
                <span>{request.bayiAdi}</span>
              </div>
              <div className="detail-item">
                <label>Territory:</label>
                <span>{request.territory || '-'}</span>
              </div>
              <div className="detail-item">
                <label>Yapılacak İş:</label>
                <span>{request.yapilacakIs}</span>
              </div>
              <div className="detail-item">
                <label>POSM Adı:</label>
                <span>{request.posmAdi || '-'}</span>
              </div>
              <div className="detail-item">
                <label>Planlanan Tarih:</label>
                <span>{request.planlananTarih || '-'}</span>
              </div>
              {request.tamamlanmaTarihi && (
                <div className="detail-item">
                  <label>Tamamlanma Tarihi:</label>
                  <span>{request.tamamlanmaTarihi}</span>
                </div>
              )}
              {request.tamamlayanKullanici && (
                <div className="detail-item">
                  <label>Tamamlayan:</label>
                  <span>{request.tamamlayanKullanici}</span>
                </div>
              )}
              {request.guncelleyenKullanici && (
                <div className="detail-item">
                  <label>Son Güncelleyen:</label>
                  <span>{request.guncelleyenKullanici}</span>
                </div>
              )}
            </div>
          </div>

          {request.yapilacakIsDetay && (
            <div className="detail-section">
              <h3>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                </svg>
                İş Detayı
              </h3>
              <div style={{ 
                padding: '16px', 
                background: '#f7fafc', 
                borderRadius: '12px', 
                border: '1px solid #e2e8f0',
                lineHeight: '1.6',
                color: '#2d3748'
              }}>
                {request.yapilacakIsDetay}
              </div>
            </div>
          )}

          {request.photos && request.photos.length > 0 && (
            <div className="detail-section">
              <h3>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
                Fotoğraflar
              </h3>
              <div className="photos-grid">
                {request.photos.map((photo, idx) => (
                  <div key={idx} className="photo-item">
                    <img
                      src={photo.url.startsWith('http') ? photo.url : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${photo.url}`}
                      alt={photo.name}
                      onError={(e) => {
                        e.target.src = 'https://via.placeholder.com/200'
                      }}
                    />
                    <p>{photo.name}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="detail-section location-section">
            <h3>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                <circle cx="12" cy="10" r="3"></circle>
              </svg>
              Konum Bilgisi
            </h3>
            {(() => {
              const lat = request.latitude
              const lng = request.longitude
              const hasCoordinates = lat != null && lng != null && 
                                     lat !== '' && lng !== '' && 
                                     lat !== undefined && lng !== undefined &&
                                     Number(lat) !== 0 && Number(lng) !== 0
              
              if (!hasCoordinates) {
                return (
                  <div className="location-warning">
                    <p>⚠️ Bu talep için konum bilgisi bulunmamaktadır.</p>
                    <p style={{ fontSize: '13px', color: '#718096', marginTop: '8px' }}>
                      Bayi bilgilerinde koordinatlar tanımlı değil.
                    </p>
                  </div>
                )
              }
              
              return (
                <div className="location-info">
                  <div className="coordinates">
                    <span className="coord-item">
                      <strong>Enlem:</strong> {String(lat)}
                    </span>
                    <span className="coord-item">
                      <strong>Boylam:</strong> {String(lng)}
                    </span>
                  </div>
                  <div className="map-buttons">
                    <button
                      onClick={() => {
                        const latStr = String(lat)
                        const lngStr = String(lng)
                        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
                        const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent)
                        
                        if (isIOS) {
                          // iOS için Apple Maps veya Google Maps
                          window.open(`maps://maps.apple.com/?q=${latStr},${lngStr}`, '_blank')
                        } else if (isMobile) {
                          // Android için Google Maps
                          window.open(`geo:${latStr},${lngStr}?q=${latStr},${lngStr}`, '_blank')
                        } else {
                          // Desktop için Google Maps web
                          window.open(`https://www.google.com/maps?q=${latStr},${lngStr}`, '_blank')
                        }
                      }}
                      className="map-btn google-maps"
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                      </svg>
                      Google Maps
                    </button>
                    <button
                      onClick={() => {
                        const latStr = String(lat)
                        const lngStr = String(lng)
                        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
                        const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent)
                        
                        if (isIOS) {
                          // iOS için Apple Maps
                          window.open(`maps://maps.apple.com/?daddr=${latStr},${lngStr}&dirflg=d`, '_blank')
                        } else if (isMobile) {
                          // Android için Google Maps directions
                          window.open(`https://www.google.com/maps/dir/?api=1&destination=${latStr},${lngStr}`, '_blank')
                        } else {
                          // Desktop için Google Maps directions
                          window.open(`https://www.google.com/maps/dir/?api=1&destination=${latStr},${lngStr}`, '_blank')
                        }
                      }}
                      className="map-btn directions"
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 2v20M2 12h20"/>
                      </svg>
                      Yol Tarifi
                    </button>
                    <button
                      onClick={() => {
                        const latStr = String(lat)
                        const lngStr = String(lng)
                        // Yandex Maps (Türkiye'de popüler)
                        window.open(`https://yandex.com.tr/harita/?pt=${lngStr},${latStr}&z=16`, '_blank')
                      }}
                      className="map-btn yandex-maps"
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                      </svg>
                      Yandex Maps
                    </button>
                  </div>
                </div>
              )
            })()}
          </div>

          <div className="detail-section">
            <h3>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
              Güncelleme
            </h3>
            <div className="update-form">
              <div className="form-group">
                <label>Durum:</label>
                <select
                  value={updateData.status}
                  onChange={(e) => setUpdateData({ ...updateData, status: e.target.value })}
                >
                  <option value="Beklemede">Beklemede</option>
                  <option value="TakvimeEklendi">Takvime Eklendi</option>
                  <option value="Tamamlandı">Tamamlandı</option>
                  <option value="İptal">İptal</option>
                </select>
              </div>
              <div className="form-group">
                <label>Öncelik:</label>
                <select
                  value={updateData.priority}
                  onChange={(e) => setUpdateData({ ...updateData, priority: e.target.value })}
                >
                  <option value="Düşük">Düşük</option>
                  <option value="Orta">Orta</option>
                  <option value="Yüksek">Yüksek</option>
                  <option value="Acil">Acil</option>
                </select>
              </div>
              <div className="form-group">
                <label>Planlanan Tarih:</label>
                <input
                  type="date"
                  value={updateData.planned_date ? (() => {
                    try {
                      // DD.MM.YYYY formatından YYYY-MM-DD'ye çevir
                      if (updateData.planned_date.includes('.')) {
                        const parts = updateData.planned_date.split('.')
                        if (parts.length === 3) {
                          return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
                        }
                      }
                      return updateData.planned_date
                    } catch {
                      return ''
                    }
                  })() : ''}
                  onChange={(e) => {
                    // YYYY-MM-DD formatından DD.MM.YYYY'ye çevir
                    if (e.target.value) {
                      const dateParts = e.target.value.split('-')
                      if (dateParts.length === 3) {
                        const dateStr = `${dateParts[2]}.${dateParts[1]}.${dateParts[0]}`
                        setUpdateData({ ...updateData, planned_date: dateStr })
                      }
                    } else {
                      setUpdateData({ ...updateData, planned_date: '' })
                    }
                  }}
                />
              </div>
              {updateData.status === 'Tamamlandı' && (
                <div className="form-group">
                  <label>Tamamlanma Tarihi: *</label>
                  <input
                    type="date"
                    value={updateData.completed_date ? (() => {
                      try {
                        // DD.MM.YYYY formatından YYYY-MM-DD'ye çevir
                        if (updateData.completed_date.includes('.')) {
                          const parts = updateData.completed_date.split('.')
                          if (parts.length === 3) {
                            return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
                          }
                        }
                        return updateData.completed_date
                      } catch {
                        return ''
                      }
                    })() : ''}
                    onChange={(e) => {
                      // YYYY-MM-DD formatından DD.MM.YYYY'ye çevir
                      if (e.target.value) {
                        const dateParts = e.target.value.split('-')
                        if (dateParts.length === 3) {
                          const dateStr = `${dateParts[2]}.${dateParts[1]}.${dateParts[0]}`
                          setUpdateData({ ...updateData, completed_date: dateStr })
                        }
                      } else {
                        setUpdateData({ ...updateData, completed_date: '' })
                      }
                    }}
                    required={updateData.status === 'Tamamlandı'}
                  />
                </div>
              )}
              <div className="form-group">
                <label>Yapılan İşler:</label>
                <textarea
                  rows="4"
                  value={updateData.job_done_desc}
                  onChange={(e) => setUpdateData({ ...updateData, job_done_desc: e.target.value })}
                  placeholder="Yapılan işlerin açıklaması..."
                />
              </div>
              
              <div className="form-group">
                <label>Fotoğraf Ekle:</label>
                <div className="photo-upload-container">
                  <label htmlFor="photo-upload-modal" className="camera-button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                      <circle cx="12" cy="13" r="4"></circle>
                    </svg>
                    <span>Fotoğraf Çek/Yükle</span>
                  </label>
                  <input
                    id="photo-upload-modal"
                    type="file"
                    accept="image/*"
                    multiple
                    capture="environment"
                    onChange={handlePhotoSelect}
                    style={{ display: 'none' }}
                  />
                  {photoPreview.length > 0 && (
                    <div className="photo-preview-container">
                      {photoPreview.map((preview, idx) => (
                        <div key={idx} className="photo-preview-item">
                          <img src={preview.preview} alt={`Preview ${idx + 1}`} />
                          <button
                            type="button"
                            onClick={() => handleRemovePhoto(idx)}
                            className="remove-photo-btn"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={handleUploadPhotos}
                        className="upload-photos-btn"
                        disabled={uploadingPhotos}
                      >
                        {uploadingPhotos ? 'Yükleniyor...' : `${photoPreview.length} Fotoğrafı Yükle`}
                      </button>
                    </div>
                  )}
                  {updateData.status === 'Tamamlandı' && (!request.photos || request.photos.length === 0) && newPhotos.length === 0 && (
                    <div className="photo-warning">
                      ⚠️ İş tamamlandı olarak işaretlenmeden önce en az bir fotoğraf yüklenmelidir.
                    </div>
                  )}
                </div>
              </div>
              
              <button
                onClick={handleUpdate}
                className="update-btn"
                disabled={
                  updating || 
                  (updateData.status === 'Tamamlandı' && (
                    (!request.photos || request.photos.length === 0) && newPhotos.length === 0 ||
                    !updateData.completed_date
                  ))
                }
              >
                {updating ? 'Güncelleniyor...' : 'Güncelle'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RequestDetailModal
