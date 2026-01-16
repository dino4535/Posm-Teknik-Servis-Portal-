import { useState, useEffect } from 'react'
import { useAuth } from '../utils/auth'
import api from '../utils/api'
import DepotSelector from '../components/DepotSelector'
import '../styles/ReportManagementPage.css'

function ReportManagementPage() {
  const { user } = useAuth()
  const [backups, setBackups] = useState([])
  const [scheduledReports, setScheduledReports] = useState([])
  const [users, setUsers] = useState([])
  const [depots, setDepots] = useState([])
  const [loading, setLoading] = useState(true)
  const [creatingBackup, setCreatingBackup] = useState(false)
  const [showReportModal, setShowReportModal] = useState(false)
  const [editingReport, setEditingReport] = useState(null)
  const [reportForm, setReportForm] = useState({
    name: '',
    report_type: 'weekly_completed',
    cron_day_of_week: '6',
    cron_hour: '23',
    cron_minute: '59',
    is_active: true,
    depot_ids: [],
    recipient_user_ids: [],
    status_filter: [],
    job_type_filter: []
  })

  useEffect(() => {
    if (user?.role === 'admin') {
      loadBackups()
      loadScheduledReports()
      loadUsers()
      loadDepots()
    }
  }, [user])

  const loadBackups = async () => {
    try {
      const response = await api.get('/backup/list-all')
      setBackups(response.data.backups)
    } catch (error) {
      console.error('Yedekler yüklenemedi:', error)
    }
  }

  const loadScheduledReports = async () => {
    try {
      const response = await api.get('/scheduled-reports/')
      setScheduledReports(response.data)
    } catch (error) {
      console.error('Otomatik raporlar yüklenemedi:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadUsers = async () => {
    try {
      const response = await api.get('/scheduled-reports/users/list')
      setUsers(response.data)
    } catch (error) {
      console.error('Kullanıcılar yüklenemedi:', error)
    }
  }

  const loadDepots = async () => {
    try {
      const response = await api.get('/admin/depots')
      setDepots(response.data)
    } catch (error) {
      console.error('Depolar yüklenemedi:', error)
    }
  }

  const handleCreateBackup = async (type = 'sql') => {
    const messages = {
      sql: 'PostgreSQL veritabanı yedeği oluşturulsun mu?',
      excel: 'Tüm tablolar Excel formatında export edilsin mi?',
      full: 'Sistemin komple yedeği oluşturulsun mu? (DB + Excel + Uploads + Config)'
    }
    
    if (!confirm(messages[type])) return

    setCreatingBackup(true)
    try {
      let response
      if (type === 'sql') {
        response = await api.post('/backup/create')
      } else if (type === 'excel') {
        response = await api.post('/backup/export-excel')
      } else if (type === 'full') {
        response = await api.post('/backup/create-full')
      }
      
      alert(response.data.message || 'İşlem başarıyla tamamlandı')
      loadBackups()
    } catch (error) {
      console.error('Yedek oluşturma hatası:', error)
      alert('İşlem başarısız: ' + (error.response?.data?.detail || error.message))
    } finally {
      setCreatingBackup(false)
    }
  }

  const handleDownloadBackup = async (filename) => {
    try {
      const response = await api.get(`/backup/download/${filename}`, {
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      alert('Yedek dosyası indirildi')
    } catch (error) {
      console.error('Yedek indirme hatası:', error)
      alert('Yedek indirme başarısız')
    }
  }

  const handleDeleteBackup = async (filename) => {
    if (!confirm(`"${filename}" yedek dosyasını silmek istediğinize emin misiniz?`)) return

    try {
      await api.delete(`/backup/${filename}`)
      alert('Yedek başarıyla silindi')
      loadBackups()
    } catch (error) {
      console.error('Yedek silme hatası:', error)
      alert('Yedek silme başarısız: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCreateReport = () => {
    setEditingReport(null)
    setReportForm({
      name: '',
      report_type: 'weekly_completed',
      cron_day_of_week: '6',
      cron_hour: '23',
      cron_minute: '59',
      is_active: true,
      depot_ids: [],
      recipient_user_ids: [],
      status_filter: [],
      job_type_filter: []
    })
    setShowReportModal(true)
  }

  const handleEditReport = (report) => {
    setEditingReport(report)
    // Cron expression'ı parse et: "day_of_week hour minute"
    const cronParts = report.cron_expression.split(' ')
    setReportForm({
      name: report.name,
      report_type: report.report_type,
      cron_day_of_week: cronParts[0] || '6',
      cron_hour: cronParts[1] || '23',
      cron_minute: cronParts[2] || '59',
      is_active: report.is_active,
      depot_ids: report.depot_ids || [],
      recipient_user_ids: report.recipient_user_ids || [],
      status_filter: report.status_filter || [],
      job_type_filter: report.job_type_filter || []
    })
    setShowReportModal(true)
  }

  const handleSaveReport = async () => {
    try {
      const cron_expression = `${reportForm.cron_day_of_week} ${reportForm.cron_hour} ${reportForm.cron_minute}`
      const reportData = {
        name: reportForm.name,
        report_type: reportForm.report_type,
        cron_expression: cron_expression,
        is_active: reportForm.is_active,
        depot_ids: reportForm.depot_ids.length > 0 ? reportForm.depot_ids : null,
        recipient_user_ids: reportForm.recipient_user_ids,
        status_filter: reportForm.status_filter.length > 0 ? reportForm.status_filter : null,
        job_type_filter: reportForm.job_type_filter.length > 0 ? reportForm.job_type_filter : null
      }

      if (editingReport) {
        await api.put(`/scheduled-reports/${editingReport.id}`, reportData)
        alert('Rapor başarıyla güncellendi')
      } else {
        await api.post('/scheduled-reports/', reportData)
        alert('Rapor başarıyla oluşturuldu')
      }

      setShowReportModal(false)
      loadScheduledReports()
    } catch (error) {
      console.error('Rapor kaydetme hatası:', error)
      alert('Rapor kaydetme başarısız: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDeleteReport = async (reportId) => {
    if (!confirm('Bu raporu silmek istediğinize emin misiniz?')) return

    try {
      await api.delete(`/scheduled-reports/${reportId}`)
      alert('Rapor başarıyla silindi')
      loadScheduledReports()
    } catch (error) {
      console.error('Rapor silme hatası:', error)
      alert('Rapor silme başarısız')
    }
  }

  const handleTestReport = async (reportId) => {
    if (!confirm('Test raporu gönderilsin mi?')) return

    try {
      await api.post(`/scheduled-reports/${reportId}/test`)
      alert('Test raporu başarıyla gönderildi')
    } catch (error) {
      console.error('Test raporu gönderme hatası:', error)
      alert('Test raporu gönderme başarısız: ' + (error.response?.data?.detail || error.message))
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
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

  const getDayName = (day) => {
    const days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
    return days[parseInt(day)] || day
  }

  const getReportTypeName = (type) => {
    const types = {
      'weekly_completed': 'Haftalık Tamamlanan İşler',
      'pending_requests': 'Bekleyen ve Planlanmış İşler',
      'custom': 'Özel Rapor'
    }
    return types[type] || type
  }

  if (user?.role !== 'admin') {
    return <div className="access-denied">Bu sayfaya erişim yetkiniz yok</div>
  }

  return (
    <div className="report-management-page">
      <div className="page-header">
        <h1>Rapor ve Yedek Yönetimi</h1>
        <div className="header-actions">
          <button
            className="btn-create-report"
            onClick={handleCreateReport}
          >
            + Yeni Otomatik Rapor
          </button>
          <div className="backup-buttons-group">
            <button
              className="btn-create-backup"
              onClick={() => handleCreateBackup('sql')}
              disabled={creatingBackup}
              title="PostgreSQL veritabanı yedeği"
            >
              {creatingBackup ? 'Oluşturuluyor...' : '📦 DB Yedeği'}
            </button>
            <button
              className="btn-create-backup-excel"
              onClick={() => handleCreateBackup('excel')}
              disabled={creatingBackup}
              title="Tüm tabloları Excel formatında export et"
            >
              {creatingBackup ? 'Oluşturuluyor...' : '📊 Excel Export'}
            </button>
            <button
              className="btn-create-backup-full"
              onClick={() => handleCreateBackup('full')}
              disabled={creatingBackup}
              title="Sistemin komple yedeği (DB + Excel + Uploads + Config)"
            >
              {creatingBackup ? 'Oluşturuluyor...' : '💾 Sistem Yedeği'}
            </button>
          </div>
        </div>
      </div>

      <div className="sections">
        <div className="section-card">
          <h2>Otomatik Raporlar</h2>
          {loading ? (
            <div className="loading-container">Yükleniyor...</div>
          ) : (
            <div className="reports-table-container">
              <table className="reports-table">
                <thead>
                  <tr>
                    <th>Rapor Adı</th>
                    <th>Tip</th>
                    <th>Zamanlama</th>
                    <th>Depolar</th>
                    <th>Alıcılar</th>
                    <th>Durum</th>
                    <th>Son Gönderim</th>
                    <th>İşlemler</th>
                  </tr>
                </thead>
                <tbody>
                  {scheduledReports.length === 0 ? (
                    <tr>
                      <td colSpan="8" style={{ textAlign: 'center', padding: '40px' }}>
                        Henüz otomatik rapor oluşturulmamış
                      </td>
                    </tr>
                  ) : (
                    scheduledReports.map((report) => (
                      <tr key={report.id}>
                        <td>{report.name}</td>
                        <td>{getReportTypeName(report.report_type)}</td>
                        <td>
                          {getDayName(report.cron_expression.split(' ')[0])} {report.cron_expression.split(' ')[1]}:{report.cron_expression.split(' ')[2]}
                        </td>
                        <td>
                          {report.depot_ids && report.depot_ids.length > 0
                            ? `${report.depot_ids.length} depo`
                            : 'Tüm Depolar'}
                        </td>
                        <td>
                          {report.recipient_user_ids.length} kullanıcı
                        </td>
                        <td>
                          <span className={`status-badge ${report.is_active ? 'active' : 'inactive'}`}>
                            {report.is_active ? 'Aktif' : 'Pasif'}
                          </span>
                        </td>
                        <td>{formatDate(report.last_sent_at)}</td>
                        <td>
                          <div className="action-buttons">
                            <button
                              className="btn-test"
                              onClick={() => handleTestReport(report.id)}
                              title="Test Gönder"
                            >
                              Test
                            </button>
                            <button
                              className="btn-edit"
                              onClick={() => handleEditReport(report)}
                              title="Düzenle"
                            >
                              Düzenle
                            </button>
                            <button
                              className="btn-delete"
                              onClick={() => handleDeleteReport(report.id)}
                              title="Sil"
                            >
                              Sil
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="section-card">
          <h2>Yedekler</h2>
          <div className="backups-table-container">
            <table className="backups-table">
              <thead>
                <tr>
                  <th>Tip</th>
                  <th>Dosya Adı</th>
                  <th>Boyut</th>
                  <th>Oluşturulma Tarihi</th>
                  <th>İşlemler</th>
                </tr>
              </thead>
              <tbody>
                {backups.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', padding: '40px' }}>
                      Henüz yedek oluşturulmamış
                    </td>
                  </tr>
                ) : (
                  backups.map((backup) => {
                    const getTypeLabel = (type) => {
                      const labels = {
                        'sql': '📦 PostgreSQL',
                        'excel': '📊 Excel',
                        'full_system': '💾 Sistem Yedeği'
                      }
                      return labels[type] || type
                    }
                    
                    return (
                      <tr key={backup.filename}>
                        <td>
                          <span className="backup-type-badge">{getTypeLabel(backup.type)}</span>
                        </td>
                        <td>{backup.filename}</td>
                        <td>{formatFileSize(backup.size)}</td>
                        <td>{formatDate(backup.created_at)}</td>
                        <td>
                          <div className="action-buttons">
                            <button
                              className="btn-download"
                              onClick={() => handleDownloadBackup(backup.filename)}
                              title="İndir"
                            >
                              İndir
                            </button>
                            <button
                              className="btn-delete-backup"
                              onClick={() => handleDeleteBackup(backup.filename)}
                              title="Sil"
                            >
                              Sil
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showReportModal && (
        <div className="modal-overlay" onClick={() => setShowReportModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingReport ? 'Rapor Düzenle' : 'Yeni Otomatik Rapor'}</h2>
            <div className="report-form">
              <div className="form-group">
                <label>Rapor Adı *</label>
                <input
                  type="text"
                  value={reportForm.name}
                  onChange={(e) => setReportForm({ ...reportForm, name: e.target.value })}
                  placeholder="Örn: Manisa Haftalık Raporu"
                />
              </div>

              <div className="form-group">
                <label>Rapor Tipi *</label>
                <select
                  value={reportForm.report_type}
                  onChange={(e) => setReportForm({ ...reportForm, report_type: e.target.value })}
                >
                  <option value="weekly_completed">Haftalık Tamamlanan İşler</option>
                  <option value="pending_requests">Bekleyen ve Planlanmış İşler</option>
                </select>
              </div>

              <div className="form-group">
                <label>Zamanlama *</label>
                <div className="cron-inputs">
                  <select
                    value={reportForm.cron_day_of_week}
                    onChange={(e) => setReportForm({ ...reportForm, cron_day_of_week: e.target.value })}
                  >
                    <option value="0">Pazartesi</option>
                    <option value="1">Salı</option>
                    <option value="2">Çarşamba</option>
                    <option value="3">Perşembe</option>
                    <option value="4">Cuma</option>
                    <option value="5">Cumartesi</option>
                    <option value="6">Pazar</option>
                  </select>
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={reportForm.cron_hour}
                    onChange={(e) => setReportForm({ ...reportForm, cron_hour: e.target.value })}
                    placeholder="Saat"
                  />
                  <input
                    type="number"
                    min="0"
                    max="59"
                    value={reportForm.cron_minute}
                    onChange={(e) => setReportForm({ ...reportForm, cron_minute: e.target.value })}
                    placeholder="Dakika"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Depolar (Boş bırakılırsa tüm depolar)</label>
                <DepotSelector
                  selectedDepotId={null}
                  onDepotChange={(depotId) => {
                    if (depotId) {
                      if (!reportForm.depot_ids.includes(depotId)) {
                        setReportForm({ ...reportForm, depot_ids: [...reportForm.depot_ids, depotId] })
                      }
                    }
                  }}
                  showAll={false}
                />
                {reportForm.depot_ids.length > 0 && (
                  <div className="selected-items">
                    {reportForm.depot_ids.map((depotId) => {
                      const depot = depots.find(d => d.id === depotId)
                      return depot ? (
                        <span key={depotId} className="selected-item">
                          {depot.name}
                          <button
                            onClick={() => {
                              setReportForm({
                                ...reportForm,
                                depot_ids: reportForm.depot_ids.filter(id => id !== depotId)
                              })
                            }}
                          >
                            ×
                          </button>
                        </span>
                      ) : null
                    })}
                  </div>
                )}
              </div>

              <div className="form-group">
                <label>Alıcı Kullanıcılar *</label>
                <div className="user-selector">
                  {users.map((u) => (
                    <label key={u.id} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={reportForm.recipient_user_ids.includes(u.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setReportForm({
                              ...reportForm,
                              recipient_user_ids: [...reportForm.recipient_user_ids, u.id]
                            })
                          } else {
                            setReportForm({
                              ...reportForm,
                              recipient_user_ids: reportForm.recipient_user_ids.filter(id => id !== u.id)
                            })
                          }
                        }}
                      />
                      {u.name} ({u.email})
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={reportForm.is_active}
                    onChange={(e) => setReportForm({ ...reportForm, is_active: e.target.checked })}
                  />
                  Aktif
                </label>
              </div>

              <div className="modal-actions">
                <button className="btn-cancel" onClick={() => setShowReportModal(false)}>
                  İptal
                </button>
                <button
                  className="btn-save"
                  onClick={handleSaveReport}
                  disabled={!reportForm.name || reportForm.recipient_user_ids.length === 0}
                >
                  {editingReport ? 'Güncelle' : 'Oluştur'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReportManagementPage
