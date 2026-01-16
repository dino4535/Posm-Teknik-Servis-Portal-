import { useState, useEffect } from 'react'
import api from '../utils/api'
import { useAuth } from '../utils/auth'
import RequestDetailModal from '../components/RequestDetailModal'
import RequestCalendar from '../components/RequestCalendar'
import DepotSelector from '../components/DepotSelector'
import '../styles/MyRequestsPage.css'

function MyRequestsPage() {
  const { user } = useAuth()
  const [requests, setRequests] = useState([])
  const [allRequests, setAllRequests] = useState([]) // Filtreleme için tüm talepler
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState('table') // 'table' or 'calendar'
  const [selectedRequestId, setSelectedRequestId] = useState(null)
  const [selectedDepotId, setSelectedDepotId] = useState(null)
  const [selectedStatus, setSelectedStatus] = useState('') // Durum filtresi
  const [selectedJobType, setSelectedJobType] = useState('') // Yapılacak İş filtresi
  const [depots, setDepots] = useState([])

  useEffect(() => {
    loadDepots()
    loadRequests()
  }, [])

  useEffect(() => {
    loadRequests()
  }, [selectedDepotId, selectedStatus, selectedJobType])

  const loadDepots = async () => {
    try {
      const response = await api.get('/admin/depots')
      setDepots(response.data)
    } catch (error) {
      console.error('Depolar yüklenemedi:', error)
      // Hata durumunda boş liste
      setDepots([])
    }
  }

  const loadRequests = async () => {
    setLoading(true)
    try {
      const params = { mine: true }
      if (selectedDepotId) {
        params.depot_id = selectedDepotId
      } else if (user?.depot_ids && user.depot_ids.length > 0) {
        // Varsayılan olarak kullanıcının ilk deposunu kullan
        params.depot_id = user.depot_ids[0]
      } else if (user?.depot_id) {
        params.depot_id = user.depot_id
      }
      const response = await api.get('/requests', { params })
      setAllRequests(response.data)
      
      // Frontend'de filtreleme yap
      let filtered = response.data
      
      if (selectedStatus) {
        filtered = filtered.filter(r => r.durum === selectedStatus)
      }
      
      if (selectedJobType) {
        filtered = filtered.filter(r => r.yapilacakIs === selectedJobType)
      }
      
      setRequests(filtered)
    } catch (error) {
      console.error('Talepler yüklenemedi:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading-container">Yükleniyor...</div>
  }

  const isTechOrAdmin = user?.role === 'tech' || user?.role === 'admin'
  const hasMultipleDepots = user?.depot_ids && user.depot_ids.length > 1

  // Benzersiz durumlar ve iş tipleri
  const uniqueStatuses = [...new Set(allRequests.map(r => r.durum))].filter(Boolean)
  const uniqueJobTypes = [...new Set(allRequests.map(r => r.yapilacakIs))].filter(Boolean)

  return (
    <div className="my-requests-page">
      <h2>Taleplerim</h2>
      
      {/* Filtreler */}
      <div className="filters-section">
        <div className="filter-group">
          <label htmlFor="depotFilter">Depo:</label>
          <select
            id="depotFilter"
            value={selectedDepotId || ''}
            onChange={(e) => setSelectedDepotId(e.target.value ? parseInt(e.target.value) : null)}
          >
            <option value="">Tüm Depolar</option>
            {depots.map(depot => (
              <option key={depot.id} value={depot.id}>{depot.name}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="statusFilter">Durum:</label>
          <select
            id="statusFilter"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            <option value="">Tüm Durumlar</option>
            {uniqueStatuses.map(status => (
              <option key={status} value={status}>{status}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="jobTypeFilter">Yapılacak İş:</label>
          <select
            id="jobTypeFilter"
            value={selectedJobType}
            onChange={(e) => setSelectedJobType(e.target.value)}
          >
            <option value="">Tüm İşler</option>
            {uniqueJobTypes.map(jobType => (
              <option key={jobType} value={jobType}>{jobType}</option>
            ))}
          </select>
        </div>

        {(selectedDepotId || selectedStatus || selectedJobType) && (
          <button
            className="clear-filters-btn"
            onClick={() => {
              setSelectedDepotId(null)
              setSelectedStatus('')
              setSelectedJobType('')
            }}
          >
            Filtreleri Temizle
          </button>
        )}
      </div>
      
      <div className="view-toggle">
        <button
          className={viewMode === 'table' ? 'active' : ''}
          onClick={() => setViewMode('table')}
        >
          Tablo Görünümü
        </button>
        <button
          className={viewMode === 'calendar' ? 'active' : ''}
          onClick={() => setViewMode('calendar')}
        >
          Takvim Görünümü
        </button>
      </div>

      {viewMode === 'table' ? (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Talep Tarihi</th>
                <th>Planlanan Tarih</th>
                <th>Bayi Adı</th>
                <th>Yapılacak İş</th>
                <th>POSM Adı</th>
                <th>Durum</th>
                <th>İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {requests.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '40px' }}>
                    Henüz talep bulunmuyor
                  </td>
                </tr>
              ) : (
                requests.map((request) => (
                  <tr key={request.id}>
                    <td>{request.talepTarihi}</td>
                    <td>
                      {request.planlananTarih ? (
                        <span className="planned-date-highlight">{request.planlananTarih}</span>
                      ) : (
                        <span className="no-plan-date">Planlanmadı</span>
                      )}
                    </td>
                    <td>{request.bayiAdi}</td>
                    <td>{request.yapilacakIs}</td>
                    <td>{request.posmAdi || '-'}</td>
                    <td>
                      <span className={`status-badge status-${request.durum.toLowerCase().replace(' ', '-')}`}>
                        {request.durum}
                      </span>
                    </td>
                    <td>
                      <div className="btn-container">
                      <button
                        className="action-btn btn-detail"
                        onClick={() => setSelectedRequestId(request.id)}
                      >
                        Detay
                      </button>
                      <button
                        className="action-btn btn-update"
                        onClick={() => setSelectedRequestId(request.id)}
                      >
                        Güncelle
                      </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="calendar-view">
          {loading ? (
            <div className="loading-container">Yükleniyor...</div>
          ) : (
            <RequestCalendar
              requests={requests}
              onEventClick={(requestId) => setSelectedRequestId(requestId)}
            />
          )}
        </div>
      )}

      {selectedRequestId && (
        <RequestDetailModal
          requestId={selectedRequestId}
          onClose={() => setSelectedRequestId(null)}
          onUpdate={() => {
            loadRequests()
            setSelectedRequestId(null)
          }}
        />
      )}
    </div>
  )
}

export default MyRequestsPage
