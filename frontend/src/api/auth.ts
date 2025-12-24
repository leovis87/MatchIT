const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const authApi = {
  getSocialLoginUrl(provider: string) {
    return `${API_BASE_URL}/auth/${provider}/login?prompt=login`
  },

  async getCurrentUser() {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/kakao/me`, {
        method: 'GET',
        credentials: 'include',
      })

      if (!response.ok) {
        return { isLoggedIn: false, user: null }
      }

      return response.json()
    } catch (error) {
      console.error('getCurrentUser failed:', error)
      return { isLoggedIn: false, user: null }
    }
  },
}