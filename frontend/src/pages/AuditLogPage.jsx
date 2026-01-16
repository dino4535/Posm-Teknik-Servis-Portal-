import { useState, useEffect } from 'react'
import { useAuth } from '../utils/auth'
import api from '../utils/api'
import '../styles/AuditLogPage.css'

function AuditLogPage() {
  const { user } = useAuth()
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState({
    action: '',
    entity_type: '',
    entity_id: '',
    start_date: '',
    end_date: ''
  })
  const [page, setPage] = useState(1)
  const [limit] = useState(50)

  useEffect(() => {
    if (user?.role === 'admin') {
      loadLogs()
    }
  }, [user, filters, page])

  const loadLogs = async () => {
    setLoading(true)
    try {
      const params = {
        limit,
        offset: (page - 1) * limit
      }
      
      if (filters.action) params.action = filters.action
      if (filters.entity_type) params.entity_type = filters.entity_type
      if (filters.entity_id) params.entity_id = parseInt(filters.entity_id)
      if (filters.start_date) {
        const parts = filters.start_date.split('.')
        if (parts.length === 3) {
          params.start_date = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}T00:00:00`
        }
      }
      if (filters.end_date) {
        const parts = filters.end_date.split('.')
        if (parts.length === 3) {
          params.end_date = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}T23:59:59`
        }
      }

      const response = await api.get('/audit-logs', { params })
      setLogs(response.data.logs)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Audit loglar yüklenemedi:', error)
      alert('Audit loglar yüklenemedi')
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPage(1)
  }

  const clearFilters = () => {
    setFilters({
      action: '',
      entity_type: '',
      entity_id: '',
      start_date: '',
      end_date: ''
    })
    setPage(1)
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return date.toLocaleString('tr-TR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (user?.role !== 'admin') {
    return <div className="access-denied">Bu sayfaya erişim yetkiniz yok</div>
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div className="audit-log-page">
      <div className="page-header">
        <h1>Audit Log (Sistem Kayıtları)</h1>
      </div>

      <div className="filters-section">
        <div className="filter-row">
          <div className="form-group">
            <label>Aksiyon:</label>
            <select
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
            >
              <option value="">Tümü</option>
              <option value="CREATE">Oluşturma</option>
              <option value="UPDATE">Güncelleme</option>
              <option value="DELETE">Silme</option>
              <option value="LOGIN">Giriş</option>
              <option value="LOGOUT">Çıkış</option>
            </select>
          </div>

          <div className="form-group">
            <label>Varlık Tipi:</label>
            <select
              value={filters.entity_type}
              onChange={(e) => handleFilterChange('entity_type', e.target.value)}
            >
              <option value="">Tümü</option>
              <option value="Request">Talep</option>
              <option value="User">Kullanıcı</option>
              <option value="POSM">POSM</option>
              <option value="Dealer">Bayi</option>
              <option value="Depot">Depo</option>
            </select>
          </div>

          <div className="form-group">
            <label>Varlık ID:</label>
            <input
              type="number"
              value={filters.entity_id}
              onChange={(e) => handleFilterChange('entity_id', e.target.value)}
              placeholder="ID girin"
            />
          </div>

          <div className="form-group">
            <label>Başlangıç Tarihi:</label>
            <input
              type="date"
              value={filters.start_date ? (() => {
                try {
                  if (filters.start_date.includes('.')) {
                    const parts = filters.start_date.split('.')
                    if (parts.length === 3) {
                      return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
                    }
                  }
                  return filters.start_date
                } catch {
                  return ''
                }
              })() : ''}
              onChange={(e) => {
                if (e.target.value) {
                  const dateParts = e.target.value.split('-')
                  if (dateParts.length === 3) {
                    handleFilterChange('start_date', `${dateParts[2]}.${dateParts[1]}.${dateParts[0]}`)
                  }
                } else {
                  handleFilterChange('start_date', '')
                }
              }}
            />
          </div>

          <div className="form-group">
            <label>Bitiş Tarihi:</label>
            <input
              type="date"
              value={filters.end_date ? (() => {
                try {
                  if (filters.end_date.includes('.')) {
                    const parts = filters.end_date.split('.')
                    if (parts.length === 3) {
                      return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
                    }
                  }
                  return filters.end_date
                } catch {
                  return ''
                }
              })() : ''}
              onChange={(e) => {
                if (e.target.value) {
                  const dateParts = e.target.value.split('-')
                  if (dateParts.length === 3) {
                    handleFilterChange('end_date', `${dateParts[2]}.${dateParts[1]}.${dateParts[0]}`)
                  }
                } else {
                  handleFilterChange('end_date', '')
                }
              }}
            />
          </div>

          <button className="btn-clear-filters" onClick={clearFilters}>
            Filtreleri Temizle
          </button>
        </div>
      </div>

      <div className="logs-info">
        <span>Toplam {total} kayıt bulundu</span>
      </div>

      {loading ? (
        <div className="loading-container">Yükleniyor...</div>
      ) : (
        <div className="logs-table-container">
          <table className="logs-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Tarih</th>
                <th>Kullanıcı</th>
                <th>Aksiyon</th>
                <th>Varlık Tipi</th>
                <th>Varlık ID</th>
                <th>Açıklama</th>
                <th>IP Adresi</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '40px' }}>
                    Kayıt bulunamadı
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td>{log.id}</td>
                    <td>{formatDate(log.created_at)}</td>
                    <td>
                      {log.user_name ? (
                        <div className="user-cell">
                          <div className="user-name">{log.user_name}</div>
                          <div className="user-email">{log.user_email}</div>
                        </div>
                      ) : (
                        <span className="system-user">Sistem</span>
                      )}
                    </td>
                    <td>
                      <span className={`action-badge action-${log.action.toLowerCase()}`}>
                        {log.action}
                      </span>
                    </td>
                    <td>{log.entity_type}</td>
                    <td>{log.entity_id || '-'}</td>
                    <td className="description-cell">
                      {log.description || '-'}
                      {log.old_values && log.new_values && (
                        <details className="change-details">
                          <summary>Değişiklikler</summary>
                          <div className="changes">
                            <div className="old-values">
                              <strong>Eski:</strong>
                              <pre>{JSON.stringify(log.old_values, null, 2)}</pre>
                            </div>
                            <div className="new-values">
                              <strong>Yeni:</strong>
                              <pre>{JSON.stringify(log.new_values, null, 2)}</pre>
                            </div>
                          </div>
                        </details>
                      )}
                    </td>
                    <td>{log.ip_address || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="page-btn"
              >
                Önceki
              </button>
              <span className="page-info">
                Sayfa {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="page-btn"
              >
                Sonraki
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AuditLogPage
