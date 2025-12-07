<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white shadow-sm">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <button
          @click="goBack"
          class="flex items-center text-gray-600 hover:text-primary-600 transition-colors"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Results
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-16">
        <div class="inline-block animate-spin rounded-full h-16 w-16 border-4 border-primary-500 border-t-transparent"></div>
        <p class="mt-4 text-gray-600">Loading article details...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-16">
        <svg class="w-20 h-20 mx-auto text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-red-600 font-medium text-lg">{{ error }}</p>
        <button @click="loadArticle" class="mt-4 btn-primary">
          Try Again
        </button>
      </div>

      <!-- Article Content -->
      <div v-else-if="article" class="space-y-6">
        <!-- Article Card -->
        <div class="bg-white rounded-2xl shadow-md p-8">
          <!-- Title -->
          <h1 class="text-3xl font-bold text-gray-900 mb-4">
            {{ article.title }}
          </h1>

          <!-- Meta Information -->
          <div class="flex flex-wrap gap-4 text-sm text-gray-600 mb-6 pb-6 border-b border-gray-200">
            <div class="flex items-center">
              <svg class="w-5 h-5 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span class="font-medium">{{ article.authors.join(', ') }}</span>
            </div>

            <div v-if="article.journal" class="flex items-center">
              <svg class="w-5 h-5 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <span>{{ article.journal }}</span>
            </div>

            <div v-if="article.publication_date" class="flex items-center">
              <svg class="w-5 h-5 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>{{ formatDate(article.publication_date) }}</span>
            </div>
          </div>

          <!-- Links -->
          <div class="flex flex-wrap gap-3 mb-6">
            <!-- Full Text Dropdown -->
            <div v-if="fullTextUrls.length > 0" class="relative">
              <button
                @click="toggleFullTextDropdown"
                class="btn-secondary inline-flex items-center"
              >
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Full Text
                <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              <!-- Dropdown Menu -->
              <div
                v-show="showFullTextDropdown"
                class="absolute left-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
              >
                <div class="py-1">
                  <button
                    v-for="(url, index) in fullTextUrls"
                    :key="index"
                    @click="handleUrlClick(url)"
                    class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                  >
                    <svg v-if="isHttpUrl(url)" class="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    <svg v-else class="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span class="truncate">{{ getUrlLabel(url, index) }}</span>
                  </button>
                </div>
              </div>
            </div>

            <a
              v-if="article.doi"
              :href="`https://doi.org/${article.doi}`"
              target="_blank"
              class="btn-secondary inline-flex items-center"
            >
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              DOI
            </a>
          </div>

          <!-- Abstract -->
          <div>
            <h2 class="text-xl font-bold text-gray-900 mb-3">Abstract</h2>
            <p class="text-gray-700 leading-relaxed whitespace-pre-line">
              {{ article.full_abstract }}
            </p>
          </div>
        </div>

        <!-- Tabs Section -->
        <div class="bg-white rounded-2xl shadow-md">
          <!-- Tab Headers -->
          <div class="border-b border-gray-200">
            <nav class="flex -mb-px">
              <button
                @click="activeTab = 'related'"
                :class="[
                  'py-4 px-6 text-sm font-medium border-b-2 transition-colors',
                  activeTab === 'related'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                <svg class="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Related Papers
              </button>
              <button
                @click="activeTab = 'references'"
                :class="[
                  'py-4 px-6 text-sm font-medium border-b-2 transition-colors',
                  activeTab === 'references'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                <svg class="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                References ({{ article.references?.length || 0 }})
              </button>
            </nav>
          </div>

          <!-- Tab Content -->
          <div class="p-6">
            <!-- Related Papers Tab -->
            <div v-show="activeTab === 'related'">
              <!-- Loading State -->
              <div v-if="relatedLoading" class="text-center py-8">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary-500 border-t-transparent"></div>
                <p class="mt-2 text-gray-600 text-sm">Finding related papers...</p>
              </div>

              <!-- Related Papers List -->
              <div v-else-if="relatedPapers.length > 0" class="space-y-4">
                <div
                  v-for="paper in relatedPapers"
                  :key="paper.id"
                  class="card p-4 hover:shadow-md transition-shadow cursor-pointer"
                  @click="navigateToArticle(paper.id)"
                >
                  <div class="flex items-start justify-between mb-2">
                    <div class="flex-1">
                      <div class="flex items-center mb-1">
                        <span class="badge-score text-xs mr-2">
                          {{ paper.similarity_score.toFixed(2) }}
                        </span>
                        <h3 class="text-base font-semibold text-gray-900 hover:text-primary-600 transition-colors line-clamp-2">
                          {{ paper.title }}
                        </h3>
                      </div>
                      <p class="text-sm text-gray-600 mb-2">
                        {{ formatAuthors(paper.authors) }}
                      </p>
                      <p class="text-sm text-gray-700 line-clamp-2">
                        {{ paper.abstract_snippet }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Empty State -->
              <div v-else class="text-center py-8 text-gray-500">
                <svg class="w-12 h-12 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>No related papers found</p>
              </div>
            </div>

            <!-- References Tab -->
            <div v-show="activeTab === 'references'">
              <div v-if="article.references && article.references.length > 0" class="space-y-4">
                <div
                  v-for="(ref, index) in article.references"
                  :key="ref.ref_id || index"
                  class="card p-4"
                >
                  <div class="flex items-start">
                    <span class="text-sm font-medium text-gray-400 mr-3">[{{ index + 1 }}]</span>
                    <div class="flex-1">
                      <h3 class="text-base font-medium text-gray-900 mb-1">
                        {{ ref.title || 'Untitled' }}
                      </h3>
                      <p v-if="ref.authors" class="text-sm text-gray-600 mb-1">
                        {{ ref.authors }}
                      </p>
                      <div class="flex flex-wrap gap-2 text-xs text-gray-500">
                        <span v-if="ref.year">{{ ref.year }}</span>
                        <span v-if="ref.venue" class="italic">{{ ref.venue }}</span>
                        <span v-if="ref.volume">Vol. {{ ref.volume }}</span>
                        <span v-if="ref.pages">pp. {{ ref.pages }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Empty State -->
              <div v-else class="text-center py-8 text-gray-500">
                <svg class="w-12 h-12 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>No references available</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSearchApi } from '@/composables/useApi'

const route = useRoute()
const router = useRouter()
const { getArticle, getRelatedArticles } = useSearchApi()

const article = ref(null)
const loading = ref(false)
const error = ref(null)
const activeTab = ref('related')

const relatedPapers = ref([])
const relatedLoading = ref(false)

// Full Text URL handling
const showFullTextDropdown = ref(false)

const fullTextUrls = computed(() => {
  if (!article.value?.full_text_url) return []
  return article.value.full_text_url.split(';').map(u => u.trim()).filter(Boolean)
})

const isHttpUrl = (url) => {
  return url?.startsWith('http://') || url?.startsWith('https://')
}

const getUrlLabel = (url, index) => {
  if (isHttpUrl(url)) {
    try {
      const urlObj = new URL(url)
      return urlObj.hostname.replace('www.', '')
    } catch {
      return `Web Link ${index + 1}`
    }
  } else {
    // JSON path
    if (url.includes('pmc_json')) {
      return 'PMC Full Text'
    } else if (url.includes('pdf_json')) {
      return 'PDF Full Text'
    }
    return 'Raw Text'
  }
}

const toggleFullTextDropdown = () => {
  showFullTextDropdown.value = !showFullTextDropdown.value
}

const handleUrlClick = (url) => {
  showFullTextDropdown.value = false
  if (isHttpUrl(url)) {
    window.open(url, '_blank')
  } else {
    // JSON path -> navigate to raw text viewer page
    router.push({ name: 'raw-text', query: { path: url } })
  }
}

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.relative')) {
    showFullTextDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  loadArticle()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

watch(() => route.params.id, () => {
  loadArticle()
})

const loadArticle = async () => {
  const articleId = route.params.id
  if (!articleId) return

  loading.value = true
  error.value = null

  try {
    const response = await getArticle(articleId)
    article.value = response.data
    // Load related papers after article is loaded
    loadRelatedPapers(articleId)
  } catch (err) {
    error.value = 'Failed to load article details'
    console.error('Error loading article:', err)
  } finally {
    loading.value = false
  }
}

const loadRelatedPapers = async (articleId) => {
  relatedLoading.value = true

  try {
    const response = await getRelatedArticles(articleId)
    relatedPapers.value = response.data.related_papers
  } catch (err) {
    console.error('Error loading related papers:', err)
  } finally {
    relatedLoading.value = false
  }
}

const navigateToArticle = (articleId) => {
  router.push({ name: 'article', params: { id: articleId } })
}

const goBack = () => {
  router.back()
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

const formatAuthors = (authors) => {
  if (!authors || authors.length === 0) return 'Unknown'
  if (authors.length === 1) return authors[0]
  if (authors.length === 2) return authors.join(' & ')
  return `${authors[0]} et al.`
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
