import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi } from './auth'

export interface User {
  id: number
  name: string
  email: string
  role: 'user' | 'admin'
  careerLevel?: string
  skills?: string[]
  desiredJobs?: string[]
}

interface AuthStore {
  user: User | null
  isLoading: boolean
  isLoggedIn: boolean
  setUser: (user: User | null) => void
  logout: () => void
  fetchCurrentUser: () => Promise<void>
  updateUserRole: (userId: number, role: 'user' | 'admin') => void
}

export const useAuth = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      isLoading: false,
      isLoggedIn: false,

      setUser: (user) => {
        set({ user, isLoggedIn: !!user })
      },

      logout: () => {
        set({ user: null, isLoggedIn: false })
      },

      fetchCurrentUser: async () => {
        set({ isLoading: true })
        try {
          const result = await authApi.getCurrentUser()
          if (result.isLoggedIn && result.user) {
            // role을 문자열/객체 여부와 관계없이 소문자로 정규화
            let role: 'user' | 'admin' = 'user'
            if (typeof result.user.role === 'string') {
              role = (result.user.role || '').toLowerCase() === 'admin' ? 'admin' : 'user'
            } else if (result.user.role && typeof result.user.role === 'object' && 'Name' in result.user.role) {
              const roleName = (result.user.role as { Name?: string }).Name || ''
              role = roleName.toLowerCase() === 'admin' ? 'admin' : 'user'
            }

            set({
              user: {
                id: result.user.user_id || result.user.id,
                name: result.user.name || '',
                email: result.user.email || '',
                role,
                careerLevel: result.user.career_level,
                skills: result.user.skills || [],
                desiredJobs: result.user.desired_jobs || [],
              },
              isLoggedIn: true,
            })
          } else {
            set({ user: null, isLoggedIn: false })
          }
        } catch (error) {
          console.error('📢 현재 사용자를 가져오지 못했습니다:', error)
          set({ user: null, isLoggedIn: false })
        } finally {
          set({ isLoading: false })
        }
      },

      updateUserRole: (userId, role) => {
        set((state) => ({
          user: state.user && state.user.id === userId ? { ...state.user, role } : state.user,
        }))
      },
    }),
    { name: 'auth' }
  )
)
