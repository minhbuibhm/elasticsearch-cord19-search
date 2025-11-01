import { ref, computed } from 'vue'
import { useApi } from './useApi'

const token = ref(localStorage.getItem('auth_token') || null)
const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

export function useAuth() {
  const api = useApi()

  const isAuthenticated = computed(() => !!token.value)

  const login = async (username) => {
    try {
      const response = await api.post('/api/auth/login', { username })

      token.value = response.data.access_token
      user.value = {
        user_id: response.data.user_id,
        username: response.data.username
      }

      localStorage.setItem('auth_token', token.value)
      localStorage.setItem('user', JSON.stringify(user.value))

      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
  }

  const getToken = () => token.value

  return {
    isAuthenticated,
    user: computed(() => user.value),
    login,
    logout,
    getToken
  }
}
