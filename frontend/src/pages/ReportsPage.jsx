import { useState, useEffect } from 'react'
import { useAuth } from '../utils/auth'
import api from '../utils/api'
import DepotSelector from '../components/DepotSelector'
import '../styles/ReportsPage.css'

function ReportsPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [detailedReport, setDetailedReport] = useState([])
  const [selectedDepotId, setSelectedDepotId] = useState(null)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [jobTypeFilter, setJobTypeFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [loadingDetailed, setLoadingDetailed] = useState(false)
  const [activeTab, setActiveTab] = useState('summary') // 'summary' or 'detailed'

  useEffect(() => {
    if (user?.role === 'admin') {
      loadStats()
    }
  }, [user, selectedDepotId, startDate, endDate])

  useEffect(() => {
    if (activeTab === 'detailed' && user?.role === 'admin') {
      loadDetailedReport()
    }
  }, [activeTab, selectedDepotId, startDate, endDate, statusFilter, jobTypeFilter])

  const loadStats = async () => {
    setLoading(true)
    try {
      const params = {}
      if (selectedDepotId) {
        params.depot_id = selectedDepotId
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
      const response = await api.get('/reports/stats', { params })
      setStats(response.data)
    } catch (error) {
      console.error('Raporlar yüklenemedi:', error)
      alert('Raporlar yüklenemedi')
    } finally {
      setLoading(false)
    }
  }

  const loadDetailedReport = async () => {
    setLoadingDetailed(true)
    try {
      const params = {}
      if (selectedDepotId) {
        params.depot_id = selectedDepotId
      }
      if (startDate) {
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
      if (statusFilter) {
        params.status_filter = statusFilter
      }
      if (jobTypeFilter) {
        params.job_type_filter = jobTypeFilter
      }
      const response = await api.get('/reports/detailed', { params })
      setDetailedReport(response.data)
    } catch (error) {
      console.error('Detaylı rapor yüklenemedi:', error)
      alert('Detaylı rapor yüklenemedi')
    } finally {
      setLoadingDetailed(false)
    }
  }

  const handleExportExcel = async () => {
    try {
      const params = new URLSearchParams()
      if (selectedDepotId) {
        params.append('depot_id', selectedDepotId.toString())
      }
      if (startDate) {
        const parts = startDate.split('.')
        if (parts.length === 3) {
          params.append('start_date', `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`)
        }
      }
      if (endDate) {
        const parts = endDate.split('.')
        if (parts.length === 3) {
          params.append('end_date', `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`)
        }
      }
      if (statusFilter) {
        params.append('status_filter', statusFilter)
      }
      if (jobTypeFilter) {
        params.append('job_type_filter', jobTypeFilter)
      }

      const response = await api.get(`/reports/export/excel?${params.toString()}`, {
        responseType: 'blob'
      })

      // Blob'u indir
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '')
      link.setAttribute('download', `detayli_rapor_${dateStr}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      alert('Excel dosyası başarıyla indirildi')
    } catch (error) {
      console.error('Excel export hatası:', error)
      alert('Excel export başarısız')
    }
  }

  if (user?.role !== 'admin') {
    return <div className="access-denied">Bu sayfaya erişim yetkiniz yok</div>
  }

  if (loading && activeTab === 'summary') {
    return <div className="loading-container">Yükleniyor...</div>
  }

  if (!stats && activeTab === 'summary') {
    return <div className="no-data">Veri bulunamadı</div>
  }

  return (
    <div className="reports-page">
      <div className="page-header">
        <h1>Raporlar</h1>
        <div className="header-actions">
          <button
            className="btn-export"
            onClick={handleExportExcel}
            disabled={loadingDetailed}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Excel'e Aktar
          </button>
        </div>
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'summary' ? 'active' : ''}`}
          onClick={() => setActiveTab('summary')}
        >
          Özet Rapor
        </button>
        <button
          className={`tab ${activeTab === 'detailed' ? 'active' : ''}`}
          onClick={() => setActiveTab('detailed')}
        >
          Detaylı Rapor
        </button>
      </div>

      <div className="filters-section">
        <DepotSelector
          selectedDepotId={selectedDepotId}
          onDepotChange={setSelectedDepotId}
          showAll={true}
        />
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
          {activeTab === 'detailed' && (
            <>
              <div className="form-group">
                <label>Durum:</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="">Tüm Durumlar</option>
                  <option value="Beklemede">Beklemede</option>
                  <option value="TakvimeEklendi">Takvime Eklendi</option>
                  <option value="Tamamlandı">Tamamlandı</option>
                  <option value="İptal">İptal</option>
                </select>
              </div>
              <div className="form-group">
                <label>İş Tipi:</label>
                <select
                  value={jobTypeFilter}
                  onChange={(e) => setJobTypeFilter(e.target.value)}
                >
                  <option value="">Tüm İşler</option>
                  <option value="Montaj">Montaj</option>
                  <option value="Demontaj">Demontaj</option>
                  <option value="Bakım">Bakım</option>
                </select>
              </div>
            </>
          )}
        </div>
      </div>

      {activeTab === 'summary' && stats && (
        <>
          <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Toplam Talep</div>
          <div className="stat-value">{stats.total_requests}</div>
        </div>
        <div className="stat-card pending">
          <div className="stat-label">Bekleyen</div>
          <div className="stat-value">{stats.pending_requests}</div>
        </div>
        <div className="stat-card planned">
          <div className="stat-label">Planlanmış</div>
          <div className="stat-value">{stats.planned_requests}</div>
        </div>
        <div className="stat-card completed">
          <div className="stat-label">Tamamlanan</div>
          <div className="stat-value">{stats.completed_requests}</div>
        </div>
        <div className="stat-card cancelled">
          <div className="stat-label">İptal</div>
          <div className="stat-value">{stats.cancelled_requests}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Tamamlanma Oranı</div>
          <div className="stat-value">{stats.completion_rate}%</div>
        </div>
        {stats.avg_completion_time_days && (
          <div className="stat-card">
            <div className="stat-label">Ort. Tamamlanma Süresi</div>
            <div className="stat-value">{stats.avg_completion_time_days} gün</div>
          </div>
        )}
      </div>

      <div className="charts-section">
        <div className="chart-card">
          <h3>Depo Bazında Dağılım</h3>
          <div className="chart-content">
            {Object.entries(stats.by_depot || {}).map(([depot, data]) => (
              <div key={depot} className="chart-item">
                <div className="chart-item-header">
                  <span className="chart-item-label">{depot}</span>
                  <span className="chart-item-value">{data.total}</span>
                </div>
                <div className="chart-bar">
                  <div 
                    className="chart-bar-fill" 
                    style={{ width: `${(data.total / stats.total_requests) * 100}%` }}
                  ></div>
                </div>
                <div className="chart-item-details">
                  <span>Bekleyen: {data.pending}</span>
                  <span>Tamamlanan: {data.completed}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-card">
          <h3>İş Tipi Bazında Dağılım</h3>
          <div className="chart-content">
            {Object.entries(stats.by_job_type || {}).map(([jobType, count]) => (
              <div key={jobType} className="chart-item">
                <div className="chart-item-header">
                  <span className="chart-item-label">{jobType}</span>
                  <span className="chart-item-value">{count}</span>
                </div>
                <div className="chart-bar">
                  <div 
                    className="chart-bar-fill" 
                    style={{ width: `${(count / stats.total_requests) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-card">
          <h3>Durum Bazında Dağılım</h3>
          <div className="chart-content">
            {Object.entries(stats.by_status || {}).map(([status, count]) => (
              <div key={status} className="chart-item">
                <div className="chart-item-header">
                  <span className="chart-item-label">{status}</span>
                  <span className="chart-item-value">{count}</span>
                </div>
                <div className="chart-bar">
                  <div 
                    className="chart-bar-fill" 
                    style={{ width: `${(count / stats.total_requests) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
        </>
      )}

      {activeTab === 'detailed' && (
        <div className="detailed-report-section">
          {loadingDetailed ? (
            <div className="loading-container">Yükleniyor...</div>
          ) : (
            <div className="detailed-table-container">
              <table className="detailed-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Talep Tarihi</th>
                    <th>Durum</th>
                    <th>Öncelik</th>
                    <th>Bayi Kodu</th>
                    <th>Bayi Adı</th>
                    <th>Territory</th>
                    <th>Depo</th>
                    <th>Yapılacak İş</th>
                    <th>POSM</th>
                    <th>Planlanan Tarih</th>
                    <th>Tamamlanma Tarihi</th>
                    <th>Oluşturan</th>
                    <th>Tamamlayan</th>
                    <th>Fotoğraf</th>
                    <th>Süre (Gün)</th>
                  </tr>
                </thead>
                <tbody>
                  {detailedReport.length === 0 ? (
                    <tr>
                      <td colSpan="16" style={{ textAlign: 'center', padding: '40px' }}>
                        Seçilen kriterlere uygun kayıt bulunamadı
                      </td>
                    </tr>
                  ) : (
                    detailedReport.map((item) => (
                      <tr key={item.id}>
                        <td>{item.id}</td>
                        <td>{item.talep_tarihi}</td>
                        <td>
                          <span className={`status-badge status-${item.durum.toLowerCase().replace(' ', '-')}`}>
                            {item.durum}
                          </span>
                        </td>
                        <td>
                          <span className={`priority-badge priority-${(item.oncelik || 'orta').toLowerCase()}`}>
                            {item.oncelik || 'Orta'}
                          </span>
                        </td>
                        <td>{item.bayi_kodu}</td>
                        <td>{item.bayi_adi}</td>
                        <td>{item.territory || '-'}</td>
                        <td>{item.depo || '-'}</td>
                        <td>{item.yapilacak_is}</td>
                        <td>{item.posm_adi || '-'}</td>
                        <td>{item.planlanan_tarih || '-'}</td>
                        <td>{item.tamamlanma_tarihi || '-'}</td>
                        <td>
                          <div className="user-info">
                            <div className="user-name">{item.olusturan_kullanici}</div>
                            <div className="user-email">{item.olusturan_email}</div>
                          </div>
                        </td>
                        <td>{item.tamamlayan_kullanici || '-'}</td>
                        <td>
                          <span className="photo-count">{item.fotoğraf_sayisi}</span>
                        </td>
                        <td>{item.tamamlanma_suresi_gun !== null ? `${item.tamamlanma_suresi_gun} gün` : '-'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ReportsPage
