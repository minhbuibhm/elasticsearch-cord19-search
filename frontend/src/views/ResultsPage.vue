<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header with Search -->
    <div class="bg-white shadow-sm sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="mb-4">
          <SearchBar
            v-model:query="searchQuery"
            placeholder="Refine your search..."
            @search="handleSearch"
          />
        </div>
        <AdvancedFilters @update="handleFiltersUpdate" />
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Results Header -->
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-gray-900">
          Search Results
          <span v-if="!loading && results.length > 0" class="text-gray-500 font-normal text-lg">
            ({{ pagination.total_results }} papers found)
          </span>
        </h2>
        <p v-if="searchQuery" class="text-gray-600 mt-1">
          Showing results for: <span class="font-medium">"{{ searchQuery }}"</span>
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-16">
        <div class="inline-block animate-spin rounded-full h-16 w-16 border-4 border-primary-500 border-t-transparent"></div>
        <p class="mt-4 text-gray-600">Searching through research papers...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-16">
        <svg class="w-20 h-20 mx-auto text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-red-600 font-medium text-lg">{{ error }}</p>
        <button @click="performSearch" class="mt-4 btn-primary">
          Try Again
        </button>
      </div>

      <!-- No Results -->
      <div v-else-if="results.length === 0" class="text-center py-16">
        <svg class="w-20 h-20 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="text-xl font-semibold text-gray-700 mb-2">No results found</h3>
        <p class="text-gray-500">Try adjusting your search query or filters</p>
      </div>

      <!-- Results Grid -->
      <div v-else class="space-y-4">
        <ResultCard
          v-for="article in results"
          :key="article.id"
          :article="article"
          @click="navigateToArticle(article.id)"
        />

        <!-- Pagination -->
        <div v-if="pagination.total_pages > 1" class="flex justify-center items-center gap-2 mt-8">
          <button
            @click="goToPage(pagination.page - 1)"
            :disabled="pagination.page === 1"
            class="px-4 py-2 rounded-lg bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          <div class="flex gap-1">
            <button
              v-for="page in visiblePages"
              :key="page"
              @click="goToPage(page)"
              class="px-4 py-2 rounded-lg border"
              :class="page === pagination.page
                ? 'bg-primary-500 text-white border-primary-500'
                : 'bg-white border-gray-300 hover:bg-gray-50'
              "
            >
              {{ page }}
            </button>
          </div>

          <button
            @click="goToPage(pagination.page + 1)"
            :disabled="pagination.page === pagination.total_pages"
            class="px-4 py-2 rounded-lg bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SearchBar from '@/components/SearchBar.vue'
import AdvancedFilters from '@/components/AdvancedFilters.vue'
import ResultCard from '@/components/ResultCard.vue'
import { useSearchApi } from '@/composables/useApi'

const route = useRoute()
const router = useRouter()
const { search } = useSearchApi()

const searchQuery = ref('')
const advancedFilters = ref({})
const results = ref([])
const pagination = ref({
  total_results: 0,
  page: 1,
  total_pages: 0,
  size: 10
})
const loading = ref(false)
const error = ref(null)

onMounted(() => {
  searchQuery.value = route.query.q || ''
  if (searchQuery.value) {
    performSearch()
  }
})

const performSearch = async (page = 1) => {
  loading.value = true
  error.value = null

  try {
    const response = await search({
      query: searchQuery.value,
      year: advancedFilters.value.year || null,
      tokenizer: advancedFilters.value.tokenizer || 'Standard',
      search_method: advancedFilters.value.search_method || 'regular',
      pagination: {
        page,
        size: 10
      }
    })

    results.value = response.data.results
    pagination.value = response.data.pagination
  } catch (err) {
    error.value = 'Failed to search papers. Please try again.'
    console.error('Search error:', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = ({ query }) => {
  searchQuery.value = query
  router.push({
    name: 'results',
    query: {
      q: query
    }
  })
  performSearch(1)
}

const handleFiltersUpdate = (filters) => {
  advancedFilters.value = filters
  performSearch(1)
}

const goToPage = (page) => {
  if (page >= 1 && page <= pagination.value.total_pages) {
    performSearch(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const visiblePages = computed(() => {
  const current = pagination.value.page
  const total = pagination.value.total_pages
  const pages = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) pages.push(i)
      pages.push('...')
      pages.push(total)
    } else if (current >= total - 3) {
      pages.push(1)
      pages.push('...')
      for (let i = total - 4; i <= total; i++) pages.push(i)
    } else {
      pages.push(1)
      pages.push('...')
      for (let i = current - 1; i <= current + 1; i++) pages.push(i)
      pages.push('...')
      pages.push(total)
    }
  }

  return pages
})

const navigateToArticle = (articleId) => {
  router.push({ name: 'article', params: { id: articleId } })
}
</script>
