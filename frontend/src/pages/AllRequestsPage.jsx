import { useState, useEffect } from 'react'
import { useAuth } from '../utils/auth'
import api from '../utils/api'
import RequestDetailModal from '../components/RequestDetailModal'
import DepotSelector from '../components/DepotSelector'
import '../styles/AllRequestsPage.css'

function AllRequestsPage() {
  const { user } = useAuth()
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedRequestId, setSelectedRequestId] = useState(null)
  const [selectedDepotId, setSelectedDepotId] = useState(null)

  useEffect(() => {
    if (user?.role === 'admin') {
      loadAllRequests()
    }
  }, [user, selectedDepotId])

  const loadAllRequests = async () => {
    try {
      const params = {}
      if (selectedDepotId) {
        params.depot_id = selectedDepotId
      }
      const response = await api.get('/requests', { params })
      setRequests(response.data)
    } catch (error) {
      console.error('Talepler yüklenemedi:', error)
    } finally {
      setLoading(false)
    }
  }

  if (user?.role !== 'admin') {
    return <div>Bu sayfaya erişim yetkiniz yok</div>
  }

  if (loading) {
    return <div className="loading-container">Yükleniyor...</div>
  }

  return (
    <div className="all-requests-page">
      <h2>Tüm Talepler</h2>
      
      <DepotSelector
        selectedDepotId={selectedDepotId}
        onDepotChange={setSelectedDepotId}
        showAll={true}
      />
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Talep Tarihi</th>
              <th>Planlanan Tarih</th>
              <th>Kullanıcı</th>
              <th>Territory</th>
              <th>Bayi Kodu</th>
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
                <td colSpan="10" style={{ textAlign: 'center', padding: '40px' }}>
                  Henüz talep bulunmuyor
                </td>
              </tr>
            ) : (
              requests.map((request) => (
                <tr key={request.id}>
                  <td>{request.talepTarihi}</td>
                  <td>{request.planlananTarih || '-'}</td>
                  <td>{request.kullanici || '-'}</td>
                  <td>{request.territory || '-'}</td>
                  <td>{request.bayiKodu}</td>
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

      {selectedRequestId && (
        <RequestDetailModal
          requestId={selectedRequestId}
          onClose={() => setSelectedRequestId(null)}
          onUpdate={() => {
            loadAllRequests()
            setSelectedRequestId(null)
          }}
        />
      )}
    </div>
  )
}

export default AllRequestsPage
