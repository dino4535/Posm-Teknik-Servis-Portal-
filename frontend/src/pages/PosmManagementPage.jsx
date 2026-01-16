import { useState, useEffect } from 'react'
import { useAuth } from '../utils/auth'
import api from '../utils/api'
import DepotSelector from '../components/DepotSelector'
import '../styles/PosmManagementPage.css'

function PosmManagementPage() {
  const { user } = useAuth()
  const [posmList, setPosmList] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedDepotId, setSelectedDepotId] = useState(user?.depot_id || null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showTransferModal, setShowTransferModal] = useState(false)
  const [editingPosm, setEditingPosm] = useState(null)
  const [depots, setDepots] = useState([])
  const [formData, setFormData] = useState({
    name: '',
    ready_count: 0,
    repair_pending_count: 0
  })
  const [transferData, setTransferData] = useState({
    posm_id: '',
    from_depot_id: '',
    to_depot_id: '',
    quantity: 1,
    transfer_type: 'ready',
    notes: ''
  })

  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'tech') {
      loadDepots()
      loadPosmList()
    }
  }, [user, selectedDepotId])

  const loadDepots = async () => {
    try {
      const response = await api.get('/admin/depots')
      setDepots(response.data)
    } catch (error) {
      console.error('Depolar yüklenemedi:', error)
    }
  }

  const loadPosmList = async () => {
    setLoading(true)
    try {
      const params = {}
      if (selectedDepotId) {
        params.depot_id = selectedDepotId
      }
      const response = await api.get('/posm', { params })
      setPosmList(response.data)
    } catch (error) {
      console.error('POSM listesi yüklenemedi:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async () => {
    if (!formData.name || !selectedDepotId) {
      alert('POSM adı ve depo seçimi zorunludur')
      return
    }

    try {
      await api.post('/posm', {
        ...formData,
        depot_id: selectedDepotId
      })
      setShowAddModal(false)
      setFormData({ name: '', ready_count: 0, repair_pending_count: 0 })
      loadPosmList()
      alert('POSM başarıyla eklendi')
    } catch (error) {
      console.error('POSM ekleme hatası:', error)
      alert(error.response?.data?.detail || 'Ekleme başarısız')
    }
  }

  const handleEdit = (posm) => {
    setEditingPosm(posm.id)
    setFormData({
      name: posm.name,
      ready_count: posm.ready_count,
      repair_pending_count: posm.repair_pending_count
    })
  }

  const handleUpdate = async (posmId) => {
    try {
      await api.patch(`/posm/${posmId}`, formData)
      setEditingPosm(null)
      loadPosmList()
      alert('POSM başarıyla güncellendi')
    } catch (error) {
      console.error('POSM güncelleme hatası:', error)
      alert(error.response?.data?.detail || 'Güncelleme başarısız')
    }
  }

  const handleDelete = async (posmId) => {
    if (!window.confirm('Bu POSM\'i silmek istediğinize emin misiniz?')) {
      return
    }

    try {
      await api.delete(`/posm/${posmId}`)
      loadPosmList()
      alert('POSM başarıyla silindi')
    } catch (error) {
      console.error('POSM silme hatası:', error)
      alert(error.response?.data?.detail || 'Silme başarısız')
    }
  }

  const handleSyncAllDepots = async () => {
    if (!window.confirm('Tüm mevcut POSM\'leri tüm depolar için oluşturmak istediğinize emin misiniz? (Stoklar 0 olarak ayarlanacak)')) {
      return
    }

    try {
      const response = await api.post('/posm/sync-all-depots')
      alert(`Senkronizasyon tamamlandı!\nOluşturulan: ${response.data.created}\nAtlanan: ${response.data.skipped}\nToplam POSM: ${response.data.total_posms}\nToplam Depo: ${response.data.total_depots}`)
      loadPosmList()
    } catch (error) {
      console.error('Senkronizasyon hatası:', error)
      alert(error.response?.data?.detail || 'Senkronizasyon başarısız')
    }
  }

  const handleTransfer = async () => {
    if (!transferData.posm_id || !transferData.from_depot_id || !transferData.to_depot_id || !transferData.quantity) {
      alert('Tüm alanları doldurunuz')
      return
    }

    if (transferData.from_depot_id === transferData.to_depot_id) {
      alert('Kaynak ve hedef depo aynı olamaz')
      return
    }

    try {
      await api.post('/posm/transfer', {
        ...transferData,
        posm_id: parseInt(transferData.posm_id),
        from_depot_id: parseInt(transferData.from_depot_id),
        to_depot_id: parseInt(transferData.to_depot_id),
        quantity: parseInt(transferData.quantity)
      })
      setShowTransferModal(false)
      setTransferData({
        posm_id: '',
        from_depot_id: '',
        to_depot_id: '',
        quantity: 1,
        transfer_type: 'ready',
        notes: ''
      })
      loadPosmList()
      alert('Transfer başarıyla tamamlandı')
    } catch (error) {
      console.error('Transfer hatası:', error)
      alert(error.response?.data?.detail || 'Transfer başarısız')
    }
  }

  const openTransferModal = (posm) => {
    setTransferData({
      posm_id: posm.id.toString(),
      from_depot_id: posm.depot_id?.toString() || selectedDepotId?.toString() || '',
      to_depot_id: '',
      quantity: 1,
      transfer_type: 'ready',
      notes: ''
    })
    setShowTransferModal(true)
  }

  if (user?.role !== 'admin' && user?.role !== 'tech') {
    return <div className="access-denied">Bu sayfaya erişim yetkiniz yok</div>
  }

  if (loading) {
    return <div className="loading-container">Yükleniyor...</div>
  }

  const isAdmin = user?.role === 'admin'
  const isTech = user?.role === 'tech'

  return (
    <div className="posm-management-page">
      <div className="page-header">
        <h2>POSM Yönetimi</h2>
        {isAdmin && (
          <div className="header-actions">
            <button
              className="btn-secondary"
              onClick={handleSyncAllDepots}
              style={{ marginRight: '12px' }}
            >
              Tüm Depolar İçin Senkronize Et
            </button>
            <button
              className="btn-primary"
              onClick={() => setShowAddModal(true)}
            >
              + Yeni POSM Ekle
            </button>
          </div>
        )}
      </div>
      
      <DepotSelector
        selectedDepotId={selectedDepotId}
        onDepotChange={setSelectedDepotId}
        showAll={isAdmin}
      />
      
      <div className="posm-table-container">
        <table className="posm-table">
          <thead>
            <tr>
              <th>POSM Adı</th>
              <th>Depo</th>
              <th>Hazır Adet</th>
              <th>Tamir Bekleyen</th>
              <th>İşlemler</th>
            </tr>
          </thead>
          <tbody>
            {posmList.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', padding: '40px' }}>
                  Henüz POSM bulunmuyor
                </td>
              </tr>
            ) : (
              posmList.map((posm) => (
                <tr key={posm.id}>
                  <td>
                    {editingPosm === posm.id && isAdmin ? (
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="edit-input"
                      />
                    ) : (
                      posm.name
                    )}
                  </td>
                  <td>
                    {depots.find(d => d.id === posm.depot_id)?.name || '-'}
                  </td>
                  <td>
                    {editingPosm === posm.id && isAdmin ? (
                      <input
                        type="number"
                        value={formData.ready_count}
                        onChange={(e) => setFormData({ ...formData, ready_count: parseInt(e.target.value) || 0 })}
                        className="edit-input"
                        min="0"
                      />
                    ) : (
                      <span className="stock-count ready">{posm.ready_count}</span>
                    )}
                  </td>
                  <td>
                    {editingPosm === posm.id && isAdmin ? (
                      <input
                        type="number"
                        value={formData.repair_pending_count}
                        onChange={(e) => setFormData({ ...formData, repair_pending_count: parseInt(e.target.value) || 0 })}
                        className="edit-input"
                        min="0"
                      />
                    ) : (
                      <span className="stock-count repair">{posm.repair_pending_count}</span>
                    )}
                  </td>
                  <td>
                    {editingPosm === posm.id && isAdmin ? (
                      <div className="btn-container">
                        <button
                          className="action-btn btn-save"
                          onClick={() => handleUpdate(posm.id)}
                        >
                          Kaydet
                        </button>
                        <button
                          className="action-btn btn-cancel"
                          onClick={() => setEditingPosm(null)}
                        >
                          İptal
                        </button>
                      </div>
                    ) : (
                      <div className="btn-container">
                        {isAdmin && (
                          <>
                            <button
                              className="action-btn btn-edit"
                              onClick={() => handleEdit(posm)}
                            >
                              Düzenle
                            </button>
                            <button
                              className="action-btn btn-transfer"
                              onClick={() => openTransferModal(posm)}
                            >
                              Transfer
                            </button>
                            <button
                              className="action-btn btn-delete"
                              onClick={() => handleDelete(posm.id)}
                            >
                              Sil
                            </button>
                          </>
                        )}
                        {isTech && (
                          <span className="view-only">Sadece Görüntüleme</span>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Yeni POSM Ekleme Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Yeni POSM Ekle</h3>
            <div className="form-group">
              <label>POSM Adı:</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="POSM adını girin"
              />
            </div>
            <div className="form-group">
              <label>Depo:</label>
              <select
                value={selectedDepotId || ''}
                onChange={(e) => setSelectedDepotId(e.target.value ? parseInt(e.target.value) : null)}
              >
                <option value="">Depo Seçin</option>
                {depots.map(depot => (
                  <option key={depot.id} value={depot.id}>{depot.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Hazır Adet:</label>
              <input
                type="number"
                value={formData.ready_count}
                onChange={(e) => setFormData({ ...formData, ready_count: parseInt(e.target.value) || 0 })}
                min="0"
              />
            </div>
            <div className="form-group">
              <label>Tamir Bekleyen Adet:</label>
              <input
                type="number"
                value={formData.repair_pending_count}
                onChange={(e) => setFormData({ ...formData, repair_pending_count: parseInt(e.target.value) || 0 })}
                min="0"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-primary" onClick={handleAdd}>
                Ekle
              </button>
              <button className="btn-secondary" onClick={() => setShowAddModal(false)}>
                İptal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Transfer Modal */}
      {showTransferModal && (
        <div className="modal-overlay" onClick={() => setShowTransferModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>POSM Transfer</h3>
            <div className="form-group">
              <label>POSM:</label>
              <select
                value={transferData.posm_id}
                onChange={(e) => setTransferData({ ...transferData, posm_id: e.target.value })}
                disabled
              >
                <option value="">POSM Seçin</option>
                {posmList.map(posm => (
                  <option key={posm.id} value={posm.id}>{posm.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Kaynak Depo:</label>
              <select
                value={transferData.from_depot_id}
                onChange={(e) => setTransferData({ ...transferData, from_depot_id: e.target.value })}
              >
                <option value="">Kaynak Depo Seçin</option>
                {depots.map(depot => (
                  <option key={depot.id} value={depot.id}>{depot.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Hedef Depo:</label>
              <select
                value={transferData.to_depot_id}
                onChange={(e) => setTransferData({ ...transferData, to_depot_id: e.target.value })}
              >
                <option value="">Hedef Depo Seçin</option>
                {depots.filter(d => d.id.toString() !== transferData.from_depot_id).map(depot => (
                  <option key={depot.id} value={depot.id}>{depot.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Transfer Tipi:</label>
              <select
                value={transferData.transfer_type}
                onChange={(e) => setTransferData({ ...transferData, transfer_type: e.target.value })}
              >
                <option value="ready">Hazır Stok</option>
                <option value="repair_pending">Tamir Bekleyen</option>
              </select>
            </div>
            <div className="form-group">
              <label>Miktar:</label>
              <input
                type="number"
                value={transferData.quantity}
                onChange={(e) => setTransferData({ ...transferData, quantity: parseInt(e.target.value) || 1 })}
                min="1"
              />
            </div>
            <div className="form-group">
              <label>Notlar (Opsiyonel):</label>
              <textarea
                value={transferData.notes}
                onChange={(e) => setTransferData({ ...transferData, notes: e.target.value })}
                placeholder="Transfer notları..."
                rows="3"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-primary" onClick={handleTransfer}>
                Transfer Et
              </button>
              <button className="btn-secondary" onClick={() => setShowTransferModal(false)}>
                İptal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PosmManagementPage
