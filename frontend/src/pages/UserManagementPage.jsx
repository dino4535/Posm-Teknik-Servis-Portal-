import { useState, useEffect } from 'react'
import api from '../utils/api'
import DepotSelector from '../components/DepotSelector'
import '../styles/UserManagementPage.css'

function UserManagementPage() {
  const [users, setUsers] = useState([])
  const [depots, setDepots] = useState([])
  const [selectedDepotId, setSelectedDepotId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'user',
    depot_id: null,  // Backward compatibility
    depot_ids: []  // Many-to-many
  })

  useEffect(() => {
    loadDepots()
    loadUsers()
  }, [selectedDepotId])

  const loadDepots = async () => {
    try {
      const response = await api.get('/admin/depots')
      setDepots(response.data)
    } catch (error) {
      console.error('Depolar yüklenemedi:', error)
    }
  }

  const loadUsers = async () => {
    setLoading(true)
    try {
      const params = selectedDepotId ? { depot_id: selectedDepotId } : {}
      const response = await api.get('/admin/users', { params })
      setUsers(response.data)
    } catch (error) {
      console.error('Kullanıcılar yüklenemedi:', error)
      alert('Kullanıcılar yüklenemedi')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingUser(null)
    setFormData({
      name: '',
      email: '',
      password: '',
      role: 'user',
      depot_id: selectedDepotId,
      depot_ids: []
    })
    setShowModal(true)
  }

  const handleEdit = (user) => {
    setEditingUser(user)
    setFormData({
      name: user.name,
      email: user.email,
      password: '',
      role: user.role,
      depot_id: user.depot_id,  // Backward compatibility
      depot_ids: user.depot_ids || []  // Many-to-many
    })
    setShowModal(true)
  }

  const handleDelete = async (userId) => {
    if (!window.confirm('Bu kullanıcıyı silmek istediğinize emin misiniz?')) {
      return
    }

    try {
      await api.delete(`/admin/users/${userId}`)
      loadUsers()
      alert('Kullanıcı başarıyla silindi')
    } catch (error) {
      alert(error.response?.data?.detail || 'Kullanıcı silinemedi')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      if (editingUser) {
        // Güncelleme
        const updateData = { ...formData }
        if (!updateData.password) {
          delete updateData.password
        }
        await api.patch(`/admin/users/${editingUser.id}`, updateData)
        alert('Kullanıcı başarıyla güncellendi')
      } else {
        // Yeni oluşturma
        await api.post('/admin/users', formData)
        alert('Kullanıcı başarıyla oluşturuldu')
      }
      setShowModal(false)
      loadUsers()
    } catch (error) {
      alert(error.response?.data?.detail || 'İşlem başarısız')
    }
  }

  const getRoleLabel = (role) => {
    const roles = {
      admin: 'Yönetici',
      tech: 'Teknik Sorumlu',
      user: 'Kullanıcı'
    }
    return roles[role] || role
  }

  const getDepotName = (depotId) => {
    const depot = depots.find(d => d.id === depotId)
    return depot ? depot.name : '-'
  }

  const getDepotNames = (depotIds) => {
    if (!depotIds || depotIds.length === 0) {
      return '-'
    }
    return depotIds.map(id => {
      const depot = depots.find(d => d.id === id)
      return depot ? depot.name : id
    }).join(', ')
  }

  const handleDepotToggle = (depotId) => {
    setFormData(prev => {
      const currentIds = prev.depot_ids || []
      if (currentIds.includes(depotId)) {
        return { ...prev, depot_ids: currentIds.filter(id => id !== depotId) }
      } else {
        return { ...prev, depot_ids: [...currentIds, depotId] }
      }
    })
  }

  return (
    <div className="user-management-page">
      <div className="page-header">
        <h1>Kullanıcı Yönetimi</h1>
        <button onClick={handleCreate} className="btn-primary">
          + Yeni Kullanıcı
        </button>
      </div>

      <DepotSelector
        selectedDepotId={selectedDepotId}
        onDepotChange={setSelectedDepotId}
        showAll={true}
      />

      {loading ? (
        <div className="loading">Yükleniyor...</div>
      ) : (
        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>İsim</th>
                <th>E-posta</th>
                <th>Rol</th>
                <th>Depo</th>
                <th>İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan="5" className="no-data">Kullanıcı bulunamadı</td>
                </tr>
              ) : (
                users.map(user => (
                  <tr key={user.id}>
                    <td>{user.name}</td>
                    <td>{user.email}</td>
                    <td>
                      <span className={`role-badge role-${user.role}`}>
                        {getRoleLabel(user.role)}
                      </span>
                    </td>
                    <td>
                      {user.depot_ids && user.depot_ids.length > 0 ? (
                        <span className="depot-badges">
                          {user.depot_ids.map(depotId => {
                            const depot = depots.find(d => d.id === depotId)
                            return depot ? (
                              <span key={depotId} className="depot-badge">{depot.name}</span>
                            ) : null
                          })}
                        </span>
                      ) : (
                        getDepotName(user.depot_id) || '-'
                      )}
                    </td>
                    <td>
                      <button
                        onClick={() => handleEdit(user)}
                        className="btn-edit"
                      >
                        Düzenle
                      </button>
                      <button
                        onClick={() => handleDelete(user.id)}
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
            <h2>{editingUser ? 'Kullanıcı Düzenle' : 'Yeni Kullanıcı'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>İsim:</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>E-posta:</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Şifre:</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder={editingUser ? "Değiştirmek için doldurun" : ""}
                  required={!editingUser}
                />
              </div>
              <div className="form-group">
                <label>Rol:</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  required
                >
                  <option value="user">Kullanıcı</option>
                  <option value="tech">Teknik Sorumlu</option>
                  <option value="admin">Yönetici</option>
                </select>
              </div>
              <div className="form-group">
                <label>Depolar (Çoklu Seçim):</label>
                <div className="depot-multi-select">
                  {depots.map(depot => (
                    <label key={depot.id} className="depot-checkbox-label">
                      <input
                        type="checkbox"
                        checked={formData.depot_ids?.includes(depot.id) || false}
                        onChange={() => handleDepotToggle(depot.id)}
                      />
                      <span className="depot-checkbox-text">{depot.name}</span>
                    </label>
                  ))}
                </div>
                {formData.depot_ids && formData.depot_ids.length > 0 && (
                  <div className="selected-depots-info">
                    Seçili depolar: {formData.depot_ids.map(id => {
                      const depot = depots.find(d => d.id === id)
                      return depot ? depot.name : id
                    }).join(', ')}
                  </div>
                )}
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">
                  İptal
                </button>
                <button type="submit" className="btn-primary">
                  {editingUser ? 'Güncelle' : 'Oluştur'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default UserManagementPage
