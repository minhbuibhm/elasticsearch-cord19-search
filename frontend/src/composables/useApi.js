import axios from 'axios'

export function useApi() {
  const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const api = axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  // Add auth token to requests
  api.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // Handle response errors
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
        window.location.reload()
      }
      return Promise.reject(error)
    }
  )

  return api
}

// Export specific API methods for convenience
export function useSearchApi() {
  const api = useApi()

  const search = (params) => api.post('/api/search', params)

  const getArticle = (id) => api.get(`/api/articles/${id}`)

  const getRelatedArticles = (id) => api.get(`/api/articles/${id}/related`)

  return {
    search,
    getArticle,
    getRelatedArticles
  }
}

export function useBookmarkApi() {
  const api = useApi()

  const getBookmarks = () => api.get('/api/bookmarks')

  const addBookmark = (articleId) => api.post('/api/bookmarks', { article_id: articleId })

  const removeBookmark = (articleId) => api.delete(`/api/bookmarks/${articleId}`)

  const checkBookmark = (articleId) => api.get(`/api/bookmarks/check/${articleId}`)

  return {
    getBookmarks,
    addBookmark,
    removeBookmark,
    checkBookmark
  }
}

export function useRecommendationApi() {
  const api = useApi()

  const getRecommendations = (limit = 10) =>
    api.get('/api/recommendations', { params: { limit } })

  return {
    getRecommendations
  }
}
