import { createRouter, createWebHistory } from 'vue-router'
import SearchPage from '@/views/SearchPage.vue'
import ResultsPage from '@/views/ResultsPage.vue'
import BookmarksPage from '@/views/BookmarksPage.vue'
import ArticleDetailPage from '@/views/ArticleDetailPage.vue'
import RawTextPage from '@/views/RawTextPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'search',
      component: SearchPage
    },
    {
      path: '/results',
      name: 'results',
      component: ResultsPage
    },
    {
      path: '/bookmarks',
      name: 'bookmarks',
      component: BookmarksPage
    },
    {
      path: '/article/:id',
      name: 'article',
      component: ArticleDetailPage
    },
    {
      path: '/raw-text',
      name: 'raw-text',
      component: RawTextPage
    }
  ]
})

export default router
