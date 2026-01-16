import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../utils/auth'
import '../styles/DashboardLayout.css'

function DashboardLayout({ children }) {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  const isAdmin = user?.role === 'admin'
  const isTech = user?.role === 'tech'

  return (
    <div className="dashboard-container">
      <div className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <img src="/Dino-Logo.png" alt="Dino Logo" className="logo" />
          <h3>Teknik Servis Portalı</h3>
        </div>
        <div className="user-info">
          <span id="userName">{user?.name || 'Kullanıcı'}</span>
          <span id="userRole">{user?.role === 'admin' ? 'Admin' : user?.role === 'tech' ? 'Teknik Sorumlu' : 'Kullanıcı'}</span>
        </div>
        <nav className="sidebar-nav">
          <ul>
            <li>
              <Link
                to="/dashboard"
                className={isActive('/dashboard') && location.pathname === '/dashboard' ? 'active' : ''}
              >
                Dashboard
              </Link>
            </li>
            <li>
              <Link
                to="/dashboard/new-request"
                className={isActive('/dashboard/new-request') ? 'active' : ''}
              >
                Yeni Talep
              </Link>
            </li>
            <li>
              <Link
                to="/dashboard/my-requests"
                className={isActive('/dashboard/my-requests') ? 'active' : ''}
              >
                Taleplerim
              </Link>
            </li>
            <li>
              <Link
                to="/dashboard/planned-work"
                className={isActive('/dashboard/planned-work') ? 'active' : ''}
              >
                Planlanmış İşler
              </Link>
            </li>
            {(isAdmin || isTech) && (
              <>
                <li>
                  <Link
                    to="/dashboard/all-requests"
                    className={isActive('/dashboard/all-requests') ? 'active' : ''}
                  >
                    Tüm Talepler
                  </Link>
                </li>
                <li>
                  <Link
                    to="/dashboard/posm-management"
                    className={isActive('/dashboard/posm-management') ? 'active' : ''}
                  >
                    POSM Yönetimi
                  </Link>
                </li>
                <li>
                  <Link
                    to="/dashboard/work-plan"
                    className={isActive('/dashboard/work-plan') ? 'active' : ''}
                  >
                    İş Planı Oluştur
                  </Link>
                </li>
              </>
            )}
            {isAdmin && (
              <>
                <li className="admin-section">
                  <span className="section-label">Admin Panel</span>
                </li>
                <li>
                  <Link
                    to="/dashboard/user-management"
                    className={isActive('/dashboard/user-management') ? 'active' : ''}
                  >
                    Kullanıcı Yönetimi
                  </Link>
                </li>
                <li>
                  <Link
                    to="/dashboard/dealer-management"
                    className={isActive('/dashboard/dealer-management') ? 'active' : ''}
                  >
                    Bayi Yönetimi
                  </Link>
                </li>
                <li>
                  <Link
                    to="/dashboard/bulk-import"
                    className={isActive('/dashboard/bulk-import') ? 'active' : ''}
                  >
                    Toplu Bayi Import
                  </Link>
                </li>
                <li>
                  <Link
                    to="/dashboard/reports"
                    className={isActive('/dashboard/reports') ? 'active' : ''}
                  >
                    Raporlar
                  </Link>
                </li>
                <li>
                  <Link
                    to="/dashboard/audit-logs"
                    className={isActive('/dashboard/audit-logs') ? 'active' : ''}
                  >
                    Audit Log
                  </Link>
                </li>
                <li>
                  <Link
                    to="/dashboard/report-management"
                    className={isActive('/dashboard/report-management') ? 'active' : ''}
                  >
                    Rapor Yönetimi
                  </Link>
                </li>
              </>
            )}
          </ul>
        </nav>
        <div className="sidebar-footer">
          <button onClick={handleLogout} className="logout-btn">
            Çıkış Yap
          </button>
        </div>
      </div>
      <div className="main-content">
        {children}
      </div>
    </div>
  )
}

export default DashboardLayout
