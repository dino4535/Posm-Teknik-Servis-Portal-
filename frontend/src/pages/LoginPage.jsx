import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../utils/auth'
import '../styles/LoginPage.css'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const result = await login(email, password)

    if (result.success) {
      navigate('/dashboard')
    } else {
      setError(result.error || 'Geçersiz e-posta veya şifre')
    }

    setLoading(false)
  }

  return (
    <div className="login-container-wrapper">
      <div className="login-container">
        <div className="login-header">
          <img src="/Dino-Logo.png" alt="Dino Logo" className="login-logo" />
          <h2>Teknik Servis Portalı</h2>
          <p>Giriş Yapın</p>
        </div>
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">E-posta</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Şifre</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <button type="submit" className="login-button" disabled={loading}>
            {loading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default LoginPage
