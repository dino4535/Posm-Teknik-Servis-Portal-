import { useState, useEffect } from 'react'
import { useAuth } from '../utils/auth'
import api from '../utils/api'
import RequestCalendar from '../components/RequestCalendar'
import RequestDetailModal from '../components/RequestDetailModal'
import DepotSelector from '../components/DepotSelector'
import '../styles/PlannedWorkPage.css'

function PlannedWorkPage() {
  const { user } = useAuth()
  const [plannedRequests, setPlannedRequests] = useState([])
  const [selectedDepotId, setSelectedDepotId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState('calendar') // 'calendar' or 'list'
  const [selectedRequestId, setSelectedRequestId] = useState(null)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  useEffect(() => {
    if (user) {
      loadPlannedRequests()
    }
  }, [user, selectedDepotId, startDate, endDate])

  const loadPlannedRequests = async () => {
    setLoading(true)
    try {
      const params = {}
      
      // Kullanıcılar sadece kendi taleplerini görebilir
      if (user?.role === 'user') {
        params.mine = true
      } else {
        // Tech/Admin için depot filtresi
        if (selectedDepotId) {
          params.depot_id = selectedDepotId
        }
      }
      
      if (startDate) {
        // DD.MM.YYYY formatından YYYY-MM-DD'ye çevir
        const parts = startDate.split('.')
        if (parts.length === 3) {
          params.start_date = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
        }
      }
      if (endDate) {
        const parts = endDate.split('.')
        if (parts.length === 3) {
          params.end_date = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
        }
      }
      const response = await api.get('/work-plan/planned', { params })
      setPlannedRequests(response.data)
    } catch (error) {
      console.error('Planlanmış işler yüklenemedi:', error)
      alert('Planlanmış işler yüklenemedi')
    } finally {
      setLoading(false)
    }
  }

  // Tüm kullanıcılar kendi planlanmış işlerini görebilir

  if (loading) {
    return <div className="loading-container">Yükleniyor...</div>
  }

  return (
    <div className="planned-work-page">
      <div className="page-header">
        <h1>Planlanmış İşler</h1>
        <p className="page-subtitle">
          {user?.role === 'user' 
            ? 'Açtığınız işlerin planlarını takvim ve liste görünümünde görüntüleyin'
            : 'Planlanmış işleri takvim ve liste görünümünde görüntüleyin ve yönetin'}
        </p>
      </div>

      <div className="filters-section">
        {(user?.role === 'admin' || user?.role === 'tech') && (
          <DepotSelector
            selectedDepotId={selectedDepotId}
            onDepotChange={setSelectedDepotId}
            showAll={user?.role === 'admin'}
          />
        )}
        
        <div className="date-filters">
          <div className="form-group">
            <label>Başlangıç Tarihi:</label>
            <input
              type="date"
              value={startDate ? (() => {
                try {
                  if (startDate.includes('.')) {
                    const parts = startDate.split('.')
                    if (parts.length === 3) {
                      return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
                    }
                  }
                  return startDate
                } catch {
                  return ''
                }
              })() : ''}
              onChange={(e) => {
                if (e.target.value) {
                  const dateParts = e.target.value.split('-')
                  if (dateParts.length === 3) {
                    const dateStr = `${dateParts[2]}.${dateParts[1]}.${dateParts[0]}`
                    setStartDate(dateStr)
                  }
                } else {
                  setStartDate('')
                }
              }}
            />
          </div>
          <div className="form-group">
            <label>Bitiş Tarihi:</label>
            <input
              type="date"
              value={endDate ? (() => {
                try {
                  if (endDate.includes('.')) {
                    const parts = endDate.split('.')
                    if (parts.length === 3) {
                      return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
                    }
                  }
                  return endDate
                } catch {
                  return ''
                }
              })() : ''}
              onChange={(e) => {
                if (e.target.value) {
                  const dateParts = e.target.value.split('-')
                  if (dateParts.length === 3) {
                    const dateStr = `${dateParts[2]}.${dateParts[1]}.${dateParts[0]}`
                    setEndDate(dateStr)
                  }
                } else {
                  setEndDate('')
                }
              }}
            />
          </div>
        </div>
      </div>

      <div className="view-toggle-container">
        <div className="view-toggle">
          <button
            className={`view-btn ${viewMode === 'calendar' ? 'active' : ''}`}
            onClick={() => setViewMode('calendar')}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
            Takvim Görünümü
          </button>
          <button
            className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="8" y1="6" x2="21" y2="6"></line>
              <line x1="8" y1="12" x2="21" y2="12"></line>
              <line x1="8" y1="18" x2="21" y2="18"></line>
              <line x1="3" y1="6" x2="3.01" y2="6"></line>
              <line x1="3" y1="12" x2="3.01" y2="12"></line>
              <line x1="3" y1="18" x2="3.01" y2="18"></line>
            </svg>
            Liste Görünümü
          </button>
        </div>
        <div className="stats-badge">
          <span className="stats-label">Toplam Planlanmış İş:</span>
          <span className="stats-value">{plannedRequests.length}</span>
        </div>
      </div>

      {viewMode === 'calendar' ? (
        <div className="calendar-view-container">
          <RequestCalendar
            requests={plannedRequests}
            onEventClick={(requestId) => setSelectedRequestId(requestId)}
          />
        </div>
      ) : (
        <div className="list-view-container">
          {plannedRequests.length === 0 ? (
            <div className="no-data">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M9 11l3 3L22 4"></path>
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
              </svg>
              <p>Planlanmış iş bulunmuyor</p>
            </div>
          ) : (
            <div className="planned-requests-grid">
              {plannedRequests.map(request => (
                <div key={request.id} className="planned-request-card">
                  <div className="card-header">
                    <div className="card-title-section">
                      <h3>{request.bayiAdi}</h3>
                      <span className="card-code">{request.bayiKodu}</span>
                    </div>
                    <span className={`status-badge status-${request.durum.toLowerCase().replace(' ', '-')}`}>
                      {request.durum}
                    </span>
                  </div>
                  
                  <div className="card-body">
                    <div className="info-row">
                      <span className="info-label">Yapılacak İş:</span>
                      <span className="info-value">{request.yapilacakIs}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Planlanan Tarih:</span>
                      <span className="info-value highlight">{request.planlananTarih || '-'}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Talep Tarihi:</span>
                      <span className="info-value">{request.talepTarihi}</span>
                    </div>
                    {request.posmAdi && (
                      <div className="info-row">
                        <span className="info-label">POSM:</span>
                        <span className="info-value">{request.posmAdi}</span>
                      </div>
                    )}
                    {request.kullanici && (
                      <div className="info-row">
                        <span className="info-label">Talep Eden:</span>
                        <span className="info-value">{request.kullanici}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="card-footer">
                    <button
                      className="action-btn btn-detail"
                      onClick={() => setSelectedRequestId(request.id)}
                    >
                      Detay Görüntüle
                    </button>
                    <button
                      className="action-btn btn-update"
                      onClick={() => setSelectedRequestId(request.id)}
                    >
                      Güncelle
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {selectedRequestId && (
        <RequestDetailModal
          requestId={selectedRequestId}
          onClose={() => setSelectedRequestId(null)}
          onUpdate={() => {
            loadPlannedRequests()
            setSelectedRequestId(null)
          }}
        />
      )}
    </div>
  )
}

export default PlannedWorkPage
