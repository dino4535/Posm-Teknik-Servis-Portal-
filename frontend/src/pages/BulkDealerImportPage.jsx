import { useState, useEffect } from 'react'
import api from '../utils/api'
import '../styles/BulkDealerImportPage.css'

function BulkDealerImportPage() {
  const [depots, setDepots] = useState([])
  const [selectedDepotId, setSelectedDepotId] = useState(null)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    loadDepots()
  }, [])

  const loadDepots = async () => {
    try {
      const response = await api.get('/admin/depots')
      setDepots(response.data)
    } catch (error) {
      console.error('Depolar yüklenemedi:', error)
    }
  }

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setResult(null)
  }

  const handleUpload = async (e) => {
    e.preventDefault()

    if (!file) {
      alert('Lütfen bir dosya seçin')
      return
    }

    if (!selectedDepotId) {
      alert('Lütfen bir depo seçin')
      return
    }

    setUploading(true)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('depot_id', selectedDepotId)

      const response = await api.post('/admin/dealers/bulk-import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        params: {
          depot_id: selectedDepotId
        }
      })

      setResult(response.data)
      setFile(null)
      document.getElementById('file-input').value = ''
      alert('Import başarıyla tamamlandı!')
    } catch (error) {
      alert(error.response?.data?.detail || 'Import başarısız')
      setResult(null)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="bulk-import-page">
      <div className="page-header">
        <h1>Toplu Bayi Import</h1>
      </div>

      <div className="import-container">
        <div className="import-info">
          <h3>Import Formatı</h3>
          <p>Excel (.xlsx, .xls) veya CSV dosyası yükleyebilirsiniz.</p>
          <p><strong>Gerekli kolonlar:</strong></p>
          <ul>
            <li><strong>Bayi Kodu</strong> (zorunlu)</li>
            <li><strong>Bayi Adı</strong> (zorunlu)</li>
            <li><strong>Territory</strong> (opsiyonel)</li>
            <li><strong>Latitude</strong> (opsiyonel)</li>
            <li><strong>Longitude</strong> (opsiyonel)</li>
          </ul>
          <p><strong>Not:</strong> Aynı depo içinde aynı bayi kodu varsa kayıt güncellenir, yoksa yeni kayıt oluşturulur.</p>
        </div>

        <form onSubmit={handleUpload} className="import-form">
          <div className="form-group">
            <label>Depo Seçiniz: *</label>
            <select
              value={selectedDepotId || ''}
              onChange={(e) => setSelectedDepotId(e.target.value ? parseInt(e.target.value) : null)}
              required
              className="depot-select"
            >
              <option value="">Depo Seçiniz</option>
              {depots.map(depot => (
                <option key={depot.id} value={depot.id}>
                  {depot.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Dosya Seçiniz: *</label>
            <input
              id="file-input"
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileChange}
              required
              className="file-input"
            />
            {file && (
              <div className="file-info">
                Seçilen dosya: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(2)} KB)
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={uploading || !file || !selectedDepotId}
            className="btn-primary"
          >
            {uploading ? 'Yükleniyor...' : 'Import Et'}
          </button>
        </form>

        {result && (
          <div className="import-result">
            <h3>Import Sonuçları</h3>
            <div className="result-stats">
              <div className="stat-item">
                <span className="stat-label">Yeni Kayıt:</span>
                <span className="stat-value success">{result.imported || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Güncellenen:</span>
                <span className="stat-value info">{result.updated || 0}</span>
              </div>
              {result.errors && result.errors.length > 0 && (
                <div className="stat-item">
                  <span className="stat-label">Hatalar:</span>
                  <span className="stat-value error">{result.errors.length}</span>
                </div>
              )}
            </div>
            {result.errors && result.errors.length > 0 && (
              <div className="errors-list">
                <h4>Hata Detayları:</h4>
                <ul>
                  {result.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default BulkDealerImportPage
