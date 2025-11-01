<template>
  <div class="border-t border-gray-200 pt-6">
    <h2 class="text-xl font-bold text-gray-900 mb-4 flex items-center">
      <svg class="w-6 h-6 mr-2 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
      Related Papers
    </h2>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary-500 border-t-transparent"></div>
      <p class="mt-2 text-gray-600 text-sm">Finding related papers...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Related Papers List -->
    <div v-else-if="relatedPapers.length > 0" class="space-y-4">
      <div
        v-for="paper in relatedPapers"
        :key="paper.id"
        class="card p-4 hover:shadow-md transition-shadow cursor-pointer"
        @click="$emit('select', paper.id)"
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
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useSearchApi } from '@/composables/useApi'

const props = defineProps({
  articleId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['select'])

const { getRelatedArticles } = useSearchApi()
const relatedPapers = ref([])
const loading = ref(false)
const error = ref(null)

watch(() => props.articleId, async (newId) => {
  if (newId) {
    await loadRelatedPapers(newId)
  }
})

onMounted(async () => {
  if (props.articleId) {
    await loadRelatedPapers(props.articleId)
  }
})

const loadRelatedPapers = async (id) => {
  loading.value = true
  error.value = null

  try {
    const response = await getRelatedArticles(id)
    relatedPapers.value = response.data.related_papers
  } catch (err) {
    error.value = 'Failed to load related papers'
    console.error('Error loading related papers:', err)
  } finally {
    loading.value = false
  }
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
