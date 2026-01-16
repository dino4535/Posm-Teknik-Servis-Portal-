import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../utils/auth'
import api from '../utils/api'
import '../styles/NewRequestPage.css'

function NewRequestPage() {
  const [territories, setTerritories] = useState([])
  const [selectedTerritory, setSelectedTerritory] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [selectedDealer, setSelectedDealer] = useState(null)
  const [posmList, setPosmList] = useState([])
  const [selectedPosm, setSelectedPosm] = useState('')
  const [posmStock, setPosmStock] = useState(null)
  const [formData, setFormData] = useState({
    job_type: '',
    job_detail: '',
    requested_date: '',
    posm_id: null,
    priority: 'Orta'
  })
  const [photos, setPhotos] = useState([])
  const [loading, setLoading] = useState(false)
  const { user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    loadTerritories()
    loadPosmList()
  }, [user])

  useEffect(() => {
    if (searchTerm && selectedTerritory) {
      searchDealers()
    } else {
      setSearchResults([])
    }
  }, [searchTerm, selectedTerritory])

  useEffect(() => {
    if (selectedPosm) {
      loadPosmStock()
    } else {
      setPosmStock(null)
    }
  }, [selectedPosm, formData.job_type])

  const loadTerritories = async () => {
    try {
      const params = {}
      // Kullanıcının depot_id'sini ekle (admin değilse)
      if (user?.role !== 'admin') {
        if (user?.depot_ids && user.depot_ids.length > 0) {
          params.depot_id = user.depot_ids[0] // İlk depo
        } else if (user?.depot_id) {
          params.depot_id = user.depot_id
        }
      }
      const response = await api.get('/territories', { params })
      setTerritories(response.data)
    } catch (error) {
      console.error('Territory\'ler yüklenemedi:', error)
    }
  }

  const loadPosmList = async () => {
    try {
      const params = {}
      // Kullanıcının depot_id'sini ekle (admin değilse)
      if (user?.role !== 'admin') {
        if (user?.depot_ids && user.depot_ids.length > 0) {
          params.depot_id = user.depot_ids[0] // İlk depo
        } else if (user?.depot_id) {
          params.depot_id = user.depot_id
        }
      }
      const response = await api.get('/posm/', { params })
      if (response.data && Array.isArray(response.data)) {
        setPosmList(response.data)
      } else {
        console.error('POSM listesi beklenmeyen formatta:', response.data)
        setPosmList([])
      }
    } catch (error) {
      console.error('POSM listesi yüklenemedi:', error)
      console.error('Hata detayı:', error.response?.data)
      setPosmList([])
    }
  }

  const searchDealers = async () => {
    try {
      const params = {
        territory: selectedTerritory,
        search: searchTerm
      }
      // Kullanıcının depot_id'sini ekle (admin değilse)
      // Backend zaten otomatik ekliyor ama açıkça belirtmek daha iyi
      if (user?.role !== 'admin') {
        if (user?.depot_ids && user.depot_ids.length > 0) {
          params.depot_id = user.depot_ids[0] // İlk depo
        } else if (user?.depot_id) {
          params.depot_id = user.depot_id
        }
      }
      const response = await api.get('/dealers', { params })
      setSearchResults(response.data)
    } catch (error) {
      console.error('Bayi araması başarısız:', error)
    }
  }

  const loadPosmStock = async () => {
    try {
      const posm = posmList.find(p => p.name === selectedPosm)
      if (posm) {
        const response = await api.get(`/posm/${posm.id}/stock`)
        setPosmStock(response.data)
      }
    } catch (error) {
      console.error('POSM stok bilgisi yüklenemedi:', error)
    }
  }

  const handleDealerSelect = (dealer) => {
    setSelectedDealer(dealer)
    setSearchTerm('')
    setSearchResults([])
  }

  const handleJobTypeChange = (e) => {
    const value = e.target.value
    setFormData({ ...formData, job_type: value })
    if (value !== 'Montaj' && value !== 'Demontaj') {
      setSelectedPosm('')
      setFormData({ ...formData, job_type: value, posm_id: null })
    }
  }

  const handlePhotoSelect = (e) => {
    const files = Array.from(e.target.files)
    setPhotos(files)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!selectedDealer) {
      alert('Lütfen bir bayi seçin')
      return
    }

    if ((formData.job_type === 'Montaj' || formData.job_type === 'Demontaj') && !selectedPosm) {
      alert('Lütfen POSM seçimi yapın')
      return
    }

    // Fotoğraf zorunlu kontrolü
    if (photos.length === 0) {
      alert('Lütfen en az bir fotoğraf yükleyin')
      return
    }

    setLoading(true)

    try {
      // Talep oluştur
      const posm = posmList.find(p => p.name === selectedPosm)
      const requestData = {
        dealer_code: selectedDealer.bayiKodu, // Backend dealer_code'dan dealer_id'ye çevirecek
        territory_id: territories.find(t => t.name === selectedTerritory)?.id || null,
        current_posm: null,
        job_type: formData.job_type,
        job_detail: formData.job_detail || null,
        requested_date: formData.requested_date,
        posm_id: posm?.id || null,
        priority: formData.priority
      }

      const response = await api.post('/requests/', requestData)

      if (response.data.success) {
        // Fotoğrafları yükle (zorunlu)
        const formDataPhotos = new FormData()
        photos.forEach(photo => {
          formDataPhotos.append('files', photo)
        })

        await api.post(`/photos/requests/${response.data.requestId}`, formDataPhotos, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        alert('Talep başarıyla oluşturuldu!')
        navigate('/dashboard/my-requests')
      }
    } catch (error) {
      console.error('Talep oluşturma hatası:', error)
      alert(error.response?.data?.detail || 'Talep oluşturulurken bir hata oluştu')
    } finally {
      setLoading(false)
    }
  }

  const showPosmSection = formData.job_type === 'Montaj' || formData.job_type === 'Demontaj'
  // Fotoğraf alanı her zaman görünür (zorunlu olduğu için)
  const showPhotoUpload = true

  return (
    <div className="new-request-page">
      <div>
        <h2>Yeni Teknik Servis Talebi</h2>
        <p style={{ color: '#718096', marginBottom: '32px', fontSize: '16px' }}>
          Lütfen talep bilgilerini eksiksiz doldurun
        </p>
        <form onSubmit={handleSubmit} className="request-form">
        <div className="form-group">
          <label htmlFor="territory">Territory</label>
          <select
            id="territory"
            value={selectedTerritory}
            onChange={(e) => setSelectedTerritory(e.target.value)}
            required
          >
            <option value="">Territory Seçiniz</option>
            {territories.map(t => (
              <option key={t.id} value={t.name}>{t.name}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="bayiSearch">Bayi Ara</label>
          <div className="bayi-search-container">
            <input
              type="text"
              id="bayiSearch"
              placeholder="Bayi kodu veya adı ile arayın..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchResults.length > 0 && (
              <div className="bayi-search-results">
                {searchResults.map((dealer, idx) => (
                  <div
                    key={idx}
                    className="search-result-item"
                    onClick={() => handleDealerSelect(dealer)}
                  >
                    <strong>{dealer.bayiKodu}</strong> - {dealer.bayiAdi}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="form-group">
          <label>Seçilen Bayi</label>
          <div className="selected-bayi">
            <input
              type="text"
              value={selectedDealer?.bayiKodu || ''}
              readOnly
              placeholder="Bayi seçiniz"
            />
            <input
              type="text"
              value={selectedDealer?.bayiAdi || ''}
              readOnly
              placeholder="Bayi adı"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="yapilacakIs">Yapılacak İş</label>
          <select
            id="yapilacakIs"
            value={formData.job_type}
            onChange={handleJobTypeChange}
            required
          >
            <option value="">Seçiniz</option>
            <option value="Montaj">Montaj</option>
            <option value="Demontaj">Demontaj</option>
            <option value="Bakım">Bakım</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="yapilacakIsDetay">Yapılacak İşler Detayı</label>
          <textarea
            id="yapilacakIsDetay"
            rows="4"
            placeholder="Yapılacak işlerin detaylarını buraya yazın..."
            value={formData.job_detail}
            onChange={(e) => setFormData({ ...formData, job_detail: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label htmlFor="istenentarih">İşin Yapılması İstenen Tarih</label>
          <input
            type="date"
            id="istenentarih"
            value={formData.requested_date}
            onChange={(e) => setFormData({ ...formData, requested_date: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="priority">Öncelik</label>
          <select
            id="priority"
            value={formData.priority}
            onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
            required
          >
            <option value="Düşük">Düşük</option>
            <option value="Orta">Orta</option>
            <option value="Yüksek">Yüksek</option>
            <option value="Acil">Acil</option>
          </select>
        </div>

        {showPosmSection && (
          <div className="posm-section">
            <div className="form-group">
              <label htmlFor="posmSelect">POSM Seçimi</label>
              <select
                id="posmSelect"
                value={selectedPosm}
                onChange={(e) => setSelectedPosm(e.target.value)}
                required
              >
                <option value="">POSM Seçiniz</option>
                {posmList.map(posm => (
                  <option key={posm.id} value={posm.name}>{posm.name}</option>
                ))}
              </select>
            </div>
            {posmStock && (
              <div className="form-group">
                <label>Mevcut Stok:</label>
                <span id="currentStock">
                  {formData.job_type === 'Montaj' 
                    ? `Hazır: ${posmStock.hazirAdet}` 
                    : `Tamir Bekleyen: ${posmStock.tamirBekleyen}`}
                </span>
              </div>
            )}
          </div>
        )}

        {showPhotoUpload && (
          <div className="photo-upload-section">
            <div className="form-group">
              <label>Fotoğraf Ekle <span style={{ color: '#e53e3e' }}>*</span></label>
              <div className="photo-upload-container">
                <label htmlFor="photoInput" className="camera-button">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                    <circle cx="12" cy="13" r="4"></circle>
                  </svg>
                  <span>Fotoğraf Çek/Yükle</span>
                </label>
                <input
                  type="file"
                  id="photoInput"
                  accept="image/*"
                  multiple
                  capture="environment"
                  onChange={handlePhotoSelect}
                  required
                  style={{ display: 'none' }}
                />
                {photos.length > 0 && (
                  <div className="selected-photos">
                    <p>{photos.length} fotoğraf seçildi</p>
                    <div className="photo-preview-list">
                      {Array.from(photos).map((photo, idx) => (
                        <div key={idx} className="photo-preview-item">
                          <img src={URL.createObjectURL(photo)} alt={`Preview ${idx + 1}`} />
                          <span>{photo.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? 'Oluşturuluyor...' : 'Talep Oluştur'}
        </button>
      </form>
      </div>
    </div>
  )
}

export default NewRequestPage
