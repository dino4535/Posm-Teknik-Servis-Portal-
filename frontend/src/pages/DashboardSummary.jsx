import { useState, useEffect } from 'react'
import { useAuth } from '../utils/auth'
import api from '../utils/api'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import '../styles/DashboardSummary.css'

function DashboardSummary() {
  const { user } = useAuth()
  const [stats, setStats] = useState({ open: 0, completed: 0, pending: 0 })
  const [chartData, setChartData] = useState([])
  const [depotStats, setDepotStats] = useState([])
  const [jobTypeStats, setJobTypeStats] = useState([])
  const [priorityStats, setPriorityStats] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (user) {
      loadStats()
      loadChartData()
    }
  }, [user])

  const loadStats = async () => {
    try {
      const params = {}
      if (user?.role !== 'admin') {
        params.user_email = user?.email
        // Kullanıcının depot_id'sini ekle
        if (user?.depot_ids && user.depot_ids.length > 0) {
          params.depot_id = user.depot_ids[0] // İlk depo
        } else if (user?.depot_id) {
          params.depot_id = user.depot_id
        }
      }
      const response = await api.get('/requests/stats', { params })
      setStats(response.data)
    } catch (error) {
      console.error('İstatistikler yüklenemedi:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadChartData = async () => {
    try {
      const params = {}
      if (user?.role !== 'admin') {
        params.user_email = user?.email
      }
      
      // Detaylı rapor verilerini al
      const response = await api.get('/reports/detailed', { params })
      const requests = response.data

      // Haftalık trend verisi (son 7 gün)
      const weeklyData = []
      const today = new Date()
      for (let i = 6; i >= 0; i--) {
        const date = new Date(today)
        date.setDate(date.getDate() - i)
        const dateStr = date.toISOString().split('T')[0]
        const dayRequests = requests.filter(r => {
          const reqDate = r.talep_tarihi?.split(' ')[0]
          if (!reqDate) return false
          const parts = reqDate.split('.')
          if (parts.length === 3) {
            const reqDateStr = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`
            return reqDateStr === dateStr
          }
          return false
        })
        weeklyData.push({
          date: date.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' }),
          tamamlanan: dayRequests.filter(r => r.durum === 'Tamamlandı').length,
          bekleyen: dayRequests.filter(r => r.durum === 'Beklemede').length,
          planlanan: dayRequests.filter(r => r.durum === 'TakvimeEklendi').length
        })
      }
      setChartData(weeklyData)

      // Depo bazında istatistikler
      const depotMap = {}
      requests.forEach(req => {
        const depot = req.depo || 'Belirtilmemiş'
        if (!depotMap[depot]) {
          depotMap[depot] = { name: depot, total: 0, completed: 0, pending: 0 }
        }
        depotMap[depot].total++
        if (req.durum === 'Tamamlandı') depotMap[depot].completed++
        if (req.durum === 'Beklemede') depotMap[depot].pending++
      })
      setDepotStats(Object.values(depotMap))

      // İş tipi bazında istatistikler
      const jobTypeMap = {}
      requests.forEach(req => {
        const jobType = req.yapilacak_is || 'Belirtilmemiş'
        if (!jobTypeMap[jobType]) {
          jobTypeMap[jobType] = 0
        }
        jobTypeMap[jobType]++
      })
      setJobTypeStats(Object.entries(jobTypeMap).map(([name, value]) => ({ name, value })))

      // Öncelik bazında istatistikler
      const priorityMap = {}
      requests.forEach(req => {
        const priority = req.oncelik || 'Orta'
        if (!priorityMap[priority]) {
          priorityMap[priority] = 0
        }
        priorityMap[priority]++
      })
      setPriorityStats(Object.entries(priorityMap).map(([name, value]) => ({ name, value })))
    } catch (error) {
      console.error('Grafik verileri yüklenemedi:', error)
    }
  }

  const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe']

  if (loading) {
    return <div className="loading-container">Yükleniyor...</div>
  }

  return (
    <div className="dashboard-summary">
      <h2>Hoş Geldiniz</h2>
      <div className="summary-cards">
        <div className="summary-card">
          <h3>Açık Talepler</h3>
          <p id="openRequestCount">{stats.open}</p>
        </div>
        <div className="summary-card">
          <h3>Tamamlanan Talepler</h3>
          <p id="completedRequestCount">{stats.completed}</p>
        </div>
        <div className="summary-card">
          <h3>Bekleyen Talepler</h3>
          <p id="pendingRequestCount">{stats.pending}</p>
        </div>
      </div>

      <div className="charts-section">
        <div className="chart-card">
          <h3>Son 7 Günlük Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="tamamlanan" stroke="#10b981" strokeWidth={2} name="Tamamlanan" />
              <Line type="monotone" dataKey="bekleyen" stroke="#fbbf24" strokeWidth={2} name="Bekleyen" />
              <Line type="monotone" dataKey="planlanan" stroke="#3b82f6" strokeWidth={2} name="Planlanan" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Depo Bazında Dağılım</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={depotStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="total" fill="#667eea" name="Toplam" />
              <Bar dataKey="completed" fill="#10b981" name="Tamamlanan" />
              <Bar dataKey="pending" fill="#fbbf24" name="Bekleyen" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>İş Tipi Dağılımı</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={jobTypeStats}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {jobTypeStats.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Öncelik Dağılımı</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={priorityStats} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" />
              <Tooltip />
              <Bar dataKey="value" fill="#764ba2" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default DashboardSummary
