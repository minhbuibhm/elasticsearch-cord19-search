<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <h1 class="text-3xl font-bold text-gray-900">Bookmarked Research</h1>
        <p class="text-gray-600 mt-1">Your saved papers and personalized recommendations</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="border-b border-gray-200 mb-6">
        <nav class="-mb-px flex space-x-8">
          <button
            @click="activeTab = 'bookmarks'"
            class="tab-button"
            :class="activeTab === 'bookmarks' ? 'tab-active' : 'tab-inactive'"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
            My Bookmarks
            <span v-if="bookmarks.length > 0" class="ml-2 px-2 py-1 text-xs rounded-full bg-primary-100 text-primary-700">
              {{ bookmarks.length }}
            </span>
          </button>

          <button
            @click="activeTab = 'recommendations'"
            class="tab-button"
            :class="activeTab === 'recommendations' ? 'tab-active' : 'tab-inactive'"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Related Research
            <span v-if="recommendations.length > 0" class="ml-2 px-2 py-1 text-xs rounded-full bg-secondary-100 text-secondary-700">
              {{ recommendations.length }}
            </span>
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div>
        <!-- My Bookmarks Tab -->
        <div v-if="activeTab === 'bookmarks'">
          <!-- Loading State -->
          <div v-if="loadingBookmarks" class="text-center py-16">
            <div class="inline-block animate-spin rounded-full h-16 w-16 border-4 border-primary-500 border-t-transparent"></div>
            <p class="mt-4 text-gray-600">Loading your bookmarks...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="bookmarksError" class="text-center py-16">
            <p class="text-red-600 font-medium">{{ bookmarksError }}</p>
          </div>

          <!-- Empty State -->
          <div v-else-if="bookmarks.length === 0" class="text-center py-16">
            <svg class="w-20 h-20 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
            <h3 class="text-xl font-semibold text-gray-700 mb-2">No bookmarks yet</h3>
            <p class="text-gray-500 mb-6">Start bookmarking papers to build your research collection</p>
            <router-link to="/" class="btn-primary">
              Discover Papers
            </router-link>
          </div>

          <!-- Bookmarks List -->
          <div v-else class="space-y-4">
            <ResultCard
              v-for="article in bookmarks"
              :key="article.id"
              :article="article"
              :bookmarked="true"
              @click="openArticleModal(article.id)"
              @bookmark-toggle="loadBookmarks"
            />
          </div>
        </div>

        <!-- Related Research Tab -->
        <div v-if="activeTab === 'recommendations'">
          <!-- Loading State -->
          <div v-if="loadingRecommendations" class="text-center py-16">
            <div class="inline-block animate-spin rounded-full h-16 w-16 border-4 border-secondary-500 border-t-transparent"></div>
            <p class="mt-4 text-gray-600">Finding related papers...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="recommendationsError" class="text-center py-16">
            <p class="text-red-600 font-medium">{{ recommendationsError }}</p>
          </div>

          <!-- Empty State (No Bookmarks) -->
          <div v-else-if="bookmarks.length === 0" class="text-center py-16">
            <svg class="w-20 h-20 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <h3 class="text-xl font-semibold text-gray-700 mb-2">No recommendations available</h3>
            <p class="text-gray-500 mb-6">Bookmark some papers to get personalized recommendations</p>
            <router-link to="/" class="btn-primary">
              Discover Papers
            </router-link>
          </div>

          <!-- Recommendations List -->
          <div v-else>
            <div class="mb-6 p-4 bg-secondary-50 rounded-lg border border-secondary-200">
              <div class="flex items-start">
                <svg class="w-6 h-6 text-secondary-600 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h3 class="font-semibold text-secondary-900 mb-1">AI-Powered Recommendations</h3>
                  <p class="text-sm text-secondary-700">
                    Based on your {{ recommendationsMeta.based_on_bookmarks }} bookmarked paper{{ recommendationsMeta.based_on_bookmarks !== 1 ? 's' : '' }},
                    we found {{ recommendations.length }} related paper{{ recommendations.length !== 1 ? 's' : '' }} you might find interesting.
                  </p>
                </div>
              </div>
            </div>

            <div class="space-y-4">
              <div
                v-for="rec in recommendations"
                :key="rec.id"
                class="card p-6 cursor-pointer hover:border-2 hover:border-secondary-200"
                @click="openArticleModal(rec.id)"
              >
                <div class="flex items-start justify-between mb-3">
                  <div class="badge-score bg-gradient-to-r from-secondary-500 to-primary-500">
                    {{ rec.relevance_score.toFixed(2) }}
                  </div>
                </div>

                <h3 class="text-xl font-bold text-gray-900 mb-2 hover:text-secondary-600">
                  {{ rec.title }}
                </h3>

                <p class="text-sm text-gray-600 mb-2">
                  {{ formatAuthors(rec.authors) }}
                </p>

                <p class="text-gray-700 leading-relaxed mb-2">
                  {{ rec.abstract_snippet }}
                </p>

                <div class="flex items-center text-sm text-secondary-600 font-medium">
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  {{ rec.reason }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Article Detail Modal -->
    <ArticleModal
      :article-id="selectedArticleId"
      :is-open="isModalOpen"
      @close="closeArticleModal"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ResultCard from '@/components/ResultCard.vue'
import ArticleModal from '@/components/ArticleModal.vue'
import { useBookmarkApi, useRecommendationApi } from '@/composables/useApi'

const { getBookmarks } = useBookmarkApi()
const { getRecommendations } = useRecommendationApi()

const activeTab = ref('bookmarks')
const bookmarks = ref([])
const recommendations = ref([])
const recommendationsMeta = ref({ based_on_bookmarks: 0 })

const loadingBookmarks = ref(false)
const loadingRecommendations = ref(false)
const bookmarksError = ref(null)
const recommendationsError = ref(null)

const selectedArticleId = ref(null)
const isModalOpen = ref(false)

onMounted(() => {
  loadBookmarks()
  loadRecommendations()
})

const loadBookmarks = async () => {
  loadingBookmarks.value = true
  bookmarksError.value = null

  try {
    const response = await getBookmarks()
    bookmarks.value = response.data.bookmarks
  } catch (err) {
    bookmarksError.value = 'Failed to load bookmarks'
    console.error('Error loading bookmarks:', err)
  } finally {
    loadingBookmarks.value = false
  }
}

const loadRecommendations = async () => {
  loadingRecommendations.value = true
  recommendationsError.value = null

  try {
    const response = await getRecommendations(10)
    recommendations.value = response.data.recommendations
    recommendationsMeta.value.based_on_bookmarks = response.data.based_on_bookmarks
  } catch (err) {
    recommendationsError.value = 'Failed to load recommendations'
    console.error('Error loading recommendations:', err)
  } finally {
    loadingRecommendations.value = false
  }
}

const openArticleModal = (articleId) => {
  selectedArticleId.value = articleId
  isModalOpen.value = true
}

const closeArticleModal = () => {
  isModalOpen.value = false
  selectedArticleId.value = null
}

const formatAuthors = (authors) => {
  if (!authors || authors.length === 0) return 'Unknown'
  if (authors.length === 1) return authors[0]
  if (authors.length === 2) return authors.join(' & ')
  return `${authors[0]} et al.`
}
</script>

<style scoped>
.tab-button {
  @apply flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors;
}

.tab-active {
  @apply border-primary-500 text-primary-600;
}

.tab-inactive {
  @apply border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300;
}
</style>
