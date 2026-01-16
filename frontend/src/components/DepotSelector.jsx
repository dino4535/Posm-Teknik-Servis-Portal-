import { useState, useEffect } from 'react'
import api from '../utils/api'
import '../styles/DepotSelector.css'

function DepotSelector({ selectedDepotId, onDepotChange, showAll = false }) {
  const [depots, setDepots] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/admin/depots')
      .then(response => {
        setDepots(response.data)
        setLoading(false)
      })
      .catch(error => {
        console.error('Depolar yüklenemedi:', error)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <div className="depot-selector-loading">Yükleniyor...</div>
  }

  return (
    <div className="depot-selector">
      <label htmlFor="depot-select">Depo:</label>
      <select
        id="depot-select"
        value={selectedDepotId || ''}
        onChange={(e) => onDepotChange(e.target.value ? parseInt(e.target.value) : null)}
        className="depot-select"
      >
        {showAll && <option value="">Tüm Depolar</option>}
        {depots.map(depot => (
          <option key={depot.id} value={depot.id}>
            {depot.name}
          </option>
        ))}
      </select>
    </div>
  )
}

export default DepotSelector
