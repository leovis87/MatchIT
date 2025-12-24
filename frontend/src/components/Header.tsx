import { useCallback, useEffect, useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { authApi } from '../services/apiService'

type NavItem = {
  label: string
  to: string
}

const navItems: NavItem[] = [
  { label: '홈', to: '/' },
  { label: '채용', to: '/jobs' },
  { label: '부트캠프', to: '/bootcamps' },
  { label: '프로필', to: '/profile' },
]

const LOGOUT_KEYS = [
  'isLogin',
  'isLoggedIn',
  'isNewUser',
  'access_token',
  'userName',
  'userEmail',
  'kakao_access_token',
  'naver_access_token',
  'google_access_token',
]

const COOKIE_NAMES = ['session_id', 'user_id', 'is_login', 'kakao_access_token', 'naver_access_token', 'google_access_token']

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const Header = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [user, setUser] = useState<{ id?: number; name?: string; email?: string; role?: string } | null>(null)

  const checkLoginStatus = useCallback(async () => {
    try {
      const result = await authApi.getCurrentUser()
      setIsLoggedIn(result.isLoggedIn === true)
      setUser(result.user || null)
    } catch (error) {
      console.error('Error checking login status:', error)
      setIsLoggedIn(false)
      setUser(null)
    }
  }, [])

  useEffect(() => {
    checkLoginStatus()
    const interval = setInterval(checkLoginStatus, 5000)
    return () => clearInterval(interval)
  }, [checkLoginStatus])

  const handleLogout = async () => {
    try {
      LOGOUT_KEYS.forEach((key) => {
        try {
          localStorage.removeItem(key)
          sessionStorage.removeItem(key)
        } catch (err) {
          console.warn('Failed to clear key', key, err)
        }
      })

      try {
        const dbs = await window.indexedDB.databases?.()
        if (dbs) dbs.forEach((db) => db.name && indexedDB.deleteDatabase(db.name))
      } catch (err) {
        console.warn('IndexedDB cleanup failed', err)
      }

      COOKIE_NAMES.forEach((name) => {
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`
        document.cookie = `${name}=; max-age=0; path=/;`
      })

      try {
        await fetch(`${API_BASE_URL}/auth/kakao/logout`, {
          method: 'GET',
          credentials: 'include',
          headers: { Accept: 'application/json' },
        })
      } catch (err) {
        console.warn('Logout request failed', err)
      }
    } finally {
      setIsLoggedIn(false)
      setTimeout(() => {
        window.location.href = '/'
      }, 200)
    }
  }

  return (
    <header className="sticky top-0 z-30 border-b border-slate-100 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 md:px-6">
        <Link to="/" className="flex items-center gap-2">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 text-base font-bold text-white shadow-soft">
            IT
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold text-primary-700">MatchIT</p>
            <p className="text-xs text-slate-500">맞춤 채용 · 부트캠프 추천</p>
          </div>
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-medium text-slate-700 md:flex">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  'transition-colors hover:text-primary-600',
                  isActive ? 'text-primary-600' : 'text-slate-700',
                ].join(' ')
              }
            >
              {item.label}
            </NavLink>
          ))}
          {/* 관리자 메뉴 - role이 admin일 때만 표시 */}
          {user?.role === 'admin' && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                [
                  'transition-colors hover:text-amber-600',
                  isActive ? 'text-amber-600 font-semibold' : 'text-slate-700',
                ].join(' ')
              }
            >
              🔧 관리자
            </NavLink>
          )}
        </nav>

        <div className="flex items-center gap-2">
          {isLoggedIn ? (
            <button
              onClick={handleLogout}
              className="hidden rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-red-200 hover:text-red-600 md:inline-flex"
            >
              로그아웃
            </button>
          ) : (
            <Link
              to="/login"
              className="hidden rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-primary-200 hover:text-primary-700 md:inline-flex"
            >
              로그인
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}

export default Header
