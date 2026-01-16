import { useState, useEffect } from 'react'
import { useAuth } from '../utils/auth'
import api from '../utils/api'
import DepotSelector from '../components/DepotSelector'
import '../styles/WorkPlanPage.css'

function WorkPlanPage() {
  const { user } = useAuth()
  const [pendingRequests, setPendingRequests] = useState([])
  const [selectedDepotId, setSelectedDepotId] = useState(user?.depot_id || null)
  const [loading, setLoading] = useState(true)
  const [selectedRequests, setSelectedRequests] = useState([])
  const [plannedDate, setPlannedDate] = useState('')
  const [planning, setPlanning] = useState(false)

  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'tech') {
      loadPendingRequests()
    }
  }, [user, selectedDepotId])

  const loadPendingRequests = async () => {
    setLoading(true)
    try {
      const params = {}
      if (selectedDepotId) {
        params.depot_id = selectedDepotId
      }
      const response = await api.get('/work-plan/pending', { params })
      setPendingRequests(response.data)
    } catch (error) {
      console.error('Bekleyen işler yüklenemedi:', error)
      alert('Bekleyen işler yüklenemedi')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectRequest = (requestId) => {
    setSelectedRequests(prev => {
      if (prev.includes(requestId)) {
        return prev.filter(id => id !== requestId)
      } else {
        return [...prev, requestId]
      }
    })
  }

  const handleSelectAll = () => {
    if (selectedRequests.length === pendingRequests.length) {
      setSelectedRequests([])
    } else {
      setSelectedRequests(pendingRequests.map(r => r.id))
    }
  }

  const handlePlanRequests = async () => {
    if (selectedRequests.length === 0) {
      alert('Lütfen en az bir iş seçin')
      return
    }

    if (!plannedDate) {
      alert('Lütfen planlanan tarih seçin')
      return
    }

    setPlanning(true)
    try {
      // Tarih formatını YYYY-MM-DD'ye çevir
      let dateStr = plannedDate
      if (dateStr.includes('.')) {
        const parts = dateStr.split('.')
        if (parts.length === 3) {
          dateStr = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
        }
      }

      const response = await api.post('/work-plan/plan', {
        request_ids: selectedRequests,
        planned_date: dateStr
      })

      alert(`${response.data.updated} iş başarıyla planlandı`)
      setSelectedRequests([])
      setPlannedDate('')
      loadPendingRequests()
    } catch (error) {
      console.error('Planlama hatası:', error)
      alert(error.response?.data?.detail || 'Planlama başarısız')
    } finally {
      setPlanning(false)
    }
  }

  if (user?.role !== 'admin' && user?.role !== 'tech') {
    return <div className="access-denied">Bu sayfaya erişim yetkiniz yok</div>
  }

  if (loading) {
    return <div className="loading-container">Yükleniyor...</div>
  }

  return (
    <div className="work-plan-page">
      <div className="page-header">
        <h1>İş Planı Oluştur</h1>
      </div>

      <DepotSelector
        selectedDepotId={selectedDepotId}
        onDepotChange={setSelectedDepotId}
        showAll={user?.role === 'admin'}
      />

      <div className="planning-section">
        <div className="planning-controls">
          <div className="form-group">
            <label>Planlanan Tarih: *</label>
            <input
              type="date"
              value={plannedDate ? (() => {
                try {
                  if (plannedDate.includes('.')) {
                    const parts = plannedDate.split('.')
                    if (parts.length === 3) {
                      return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
                    }
                  }
                  return plannedDate
                } catch {
                  return ''
                }
              })() : ''}
              onChange={(e) => {
                if (e.target.value) {
                  const dateParts = e.target.value.split('-')
                  if (dateParts.length === 3) {
                    const dateStr = `${dateParts[2]}.${dateParts[1]}.${dateParts[0]}`
                    setPlannedDate(dateStr)
                  }
                } else {
                  setPlannedDate('')
                }
              }}
              required
            />
          </div>
          <button
            onClick={handlePlanRequests}
            className="plan-btn"
            disabled={planning || selectedRequests.length === 0 || !plannedDate}
          >
            {planning ? 'Planlanıyor...' : `Seçili ${selectedRequests.length} İşi Planla`}
          </button>
        </div>
      </div>

      <div className="requests-section">
        <div className="section-header">
          <h2>Bekleyen İşler ({pendingRequests.length})</h2>
          {pendingRequests.length > 0 && (
            <button onClick={handleSelectAll} className="select-all-btn">
              {selectedRequests.length === pendingRequests.length ? 'Tümünü Kaldır' : 'Tümünü Seç'}
            </button>
          )}
        </div>

        {pendingRequests.length === 0 ? (
          <div className="no-data">Bekleyen iş bulunmuyor</div>
        ) : (
          <div className="requests-table-container">
            <table className="requests-table">
              <thead>
                <tr>
                  <th style={{ width: '40px' }}>
                    <input
                      type="checkbox"
                      checked={selectedRequests.length === pendingRequests.length && pendingRequests.length > 0}
                      onChange={handleSelectAll}
                    />
                  </th>
                  <th>Talep Tarihi</th>
                  <th>Bayi</th>
                  <th>Yapılacak İş</th>
                  <th>İstenen Tarih</th>
                  <th>Kullanıcı</th>
                  <th>İşlemler</th>
                </tr>
              </thead>
              <tbody>
                {pendingRequests.map(request => (
                  <tr key={request.id} className={selectedRequests.includes(request.id) ? 'selected' : ''}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedRequests.includes(request.id)}
                        onChange={() => handleSelectRequest(request.id)}
                      />
                    </td>
                    <td>{request.talepTarihi}</td>
                    <td>
                      <div>
                        <strong>{request.bayiKodu}</strong>
                        <br />
                        <small>{request.bayiAdi}</small>
                      </div>
                    </td>
                    <td>
                      <span className={`job-type-badge job-${request.yapilacakIs.toLowerCase()}`}>
                        {request.yapilacakIs}
                      </span>
                    </td>
                    <td>{request.istenentarih}</td>
                    <td>{request.kullanici || '-'}</td>
                    <td>
                      <button
                        onClick={() => handleSelectRequest(request.id)}
                        className="action-btn"
                      >
                        {selectedRequests.includes(request.id) ? 'Seçimi Kaldır' : 'Seç'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default WorkPlanPage
