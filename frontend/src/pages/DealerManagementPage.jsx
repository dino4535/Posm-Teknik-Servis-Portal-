import { useState, useEffect } from 'react'
import api from '../utils/api'
import DepotSelector from '../components/DepotSelector'
import '../styles/DealerManagementPage.css'

function DealerManagementPage() {
  const [dealers, setDealers] = useState([])
  const [depots, setDepots] = useState([])
  const [territories, setTerritories] = useState([])
  const [selectedDepotId, setSelectedDepotId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingDealer, setEditingDealer] = useState(null)
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    territory_id: null,
    depot_id: null,
    latitude: '',
    longitude: ''
  })

  useEffect(() => {
    loadDepots()
    loadTerritories()
    loadDealers()
  }, [selectedDepotId])

  const loadDepots = async () => {
    try {
      const response = await api.get('/admin/depots')
      setDepots(response.data)
    } catch (error) {
      console.error('Depolar yüklenemedi:', error)
    }
  }

  const loadTerritories = async () => {
    try {
      const response = await api.get('/territories')
      setTerritories(response.data)
    } catch (error) {
      console.error('Territory\'ler yüklenemedi:', error)
    }
  }

  const loadDealers = async () => {
    setLoading(true)
    try {
      const params = selectedDepotId ? { depot_id: selectedDepotId } : {}
      const response = await api.get('/admin/dealers', { params })
      setDealers(response.data)
    } catch (error) {
      console.error('Bayiler yüklenemedi:', error)
      alert('Bayiler yüklenemedi')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingDealer(null)
    setFormData({
      code: '',
      name: '',
      territory_id: null,
      depot_id: selectedDepotId,
      latitude: '',
      longitude: ''
    })
    setShowModal(true)
  }

  const handleEdit = (dealer) => {
    setEditingDealer(dealer)
    setFormData({
      code: dealer.code,
      name: dealer.name,
      territory_id: dealer.territory_id,
      depot_id: dealer.depot_id,
      latitude: dealer.latitude || '',
      longitude: dealer.longitude || ''
    })
    setShowModal(true)
  }

  const handleDelete = async (dealerId) => {
    if (!window.confirm('Bu bayi kaydını silmek istediğinize emin misiniz?')) {
      return
    }

    try {
      await api.delete(`/admin/dealers/${dealerId}`)
      loadDealers()
      alert('Bayi başarıyla silindi')
    } catch (error) {
      alert(error.response?.data?.detail || 'Bayi silinemedi')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      const submitData = {
        ...formData,
        latitude: formData.latitude ? parseFloat(formData.latitude) : null,
        longitude: formData.longitude ? parseFloat(formData.longitude) : null,
        territory_id: formData.territory_id || null,
        depot_id: formData.depot_id || null
      }

      if (editingDealer) {
        await api.patch(`/admin/dealers/${editingDealer.id}`, submitData)
        alert('Bayi başarıyla güncellendi')
      } else {
        await api.post('/admin/dealers', submitData)
        alert('Bayi başarıyla oluşturuldu')
      }
      setShowModal(false)
      loadDealers()
    } catch (error) {
      alert(error.response?.data?.detail || 'İşlem başarısız')
    }
  }

  const getTerritoryName = (territoryId) => {
    const territory = territories.find(t => t.id === territoryId)
    return territory ? territory.name : '-'
  }

  const getDepotName = (depotId) => {
    const depot = depots.find(d => d.id === depotId)
    return depot ? depot.name : '-'
  }

  return (
    <div className="dealer-management-page">
      <div className="page-header">
        <h1>Bayi Yönetimi</h1>
        <div>
          <button onClick={handleCreate} className="btn-primary">
            + Yeni Bayi
          </button>
        </div>
      </div>

      <DepotSelector
        selectedDepotId={selectedDepotId}
        onDepotChange={setSelectedDepotId}
        showAll={true}
      />

      {loading ? (
        <div className="loading">Yükleniyor...</div>
      ) : (
        <div className="dealers-table-container">
          <table className="dealers-table">
            <thead>
              <tr>
                <th>Bayi Kodu</th>
                <th>Bayi Adı</th>
                <th>Territory</th>
                <th>Depo</th>
                <th>Koordinatlar</th>
                <th>İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {dealers.length === 0 ? (
                <tr>
                  <td colSpan="6" className="no-data">Bayi bulunamadı</td>
                </tr>
              ) : (
                dealers.map(dealer => (
                  <tr key={dealer.id}>
                    <td>{dealer.code}</td>
                    <td>{dealer.name}</td>
                    <td>{getTerritoryName(dealer.territory_id)}</td>
                    <td>{getDepotName(dealer.depot_id)}</td>
                    <td>
                      {dealer.latitude && dealer.longitude
                        ? `${dealer.latitude}, ${dealer.longitude}`
                        : '-'}
                    </td>
                    <td>
                      <button
                        onClick={() => handleEdit(dealer)}
                        className="btn-edit"
                      >
                        Düzenle
                      </button>
                      <button
                        onClick={() => handleDelete(dealer.id)}
                        className="btn-delete"
                      >
                        Sil
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingDealer ? 'Bayi Düzenle' : 'Yeni Bayi'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Bayi Kodu:</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Bayi Adı:</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Territory:</label>
                <select
                  value={formData.territory_id || ''}
                  onChange={(e) => setFormData({ ...formData, territory_id: e.target.value ? parseInt(e.target.value) : null })}
                >
                  <option value="">Territory Seçiniz</option>
                  {territories.map(territory => (
                    <option key={territory.id} value={territory.id}>
                      {territory.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Depo:</label>
                <select
                  value={formData.depot_id || ''}
                  onChange={(e) => setFormData({ ...formData, depot_id: e.target.value ? parseInt(e.target.value) : null })}
                  required
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
                <label>Latitude:</label>
                <input
                  type="number"
                  step="any"
                  value={formData.latitude}
                  onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                  placeholder="38.6191"
                />
              </div>
              <div className="form-group">
                <label>Longitude:</label>
                <input
                  type="number"
                  step="any"
                  value={formData.longitude}
                  onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                  placeholder="27.4289"
                />
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">
                  İptal
                </button>
                <button type="submit" className="btn-primary">
                  {editingDealer ? 'Güncelle' : 'Oluştur'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default DealerManagementPage
