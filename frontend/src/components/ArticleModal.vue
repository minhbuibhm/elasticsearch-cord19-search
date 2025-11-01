<template>
  <transition name="modal">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="close"
    >
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-black bg-opacity-60 transition-opacity"></div>

      <!-- Modal Content -->
      <div class="flex min-h-screen items-center justify-center p-4">
        <div
          class="relative bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
          @click.stop
        >
          <!-- Close Button -->
          <button
            @click="close"
            class="sticky top-4 right-4 float-right z-10 p-2 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <!-- Loading State -->
          <div v-if="loading" class="p-12 text-center">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
            <p class="mt-4 text-gray-600">Loading article details...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="p-12 text-center">
            <svg class="w-16 h-16 mx-auto text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-red-600 font-medium">{{ error }}</p>
          </div>

          <!-- Article Content -->
          <div v-else-if="article" class="p-8">
            <!-- Title -->
            <h1 class="text-3xl font-bold text-gray-900 mb-4 pr-8">
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
              <a
                v-if="article.full_text_url"
                :href="article.full_text_url"
                target="_blank"
                class="btn-secondary inline-flex items-center"
              >
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Full Text
              </a>

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
            <div class="mb-8">
              <h2 class="text-xl font-bold text-gray-900 mb-3">Abstract</h2>
              <p class="text-gray-700 leading-relaxed whitespace-pre-line">
                {{ article.full_abstract }}
              </p>
            </div>

            <!-- Related Papers -->
            <RelatedPapers :article-id="article.id" />
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useSearchApi } from '@/composables/useApi'
import RelatedPapers from './RelatedPapers.vue'

const props = defineProps({
  articleId: {
    type: String,
    default: null
  },
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const { getArticle } = useSearchApi()
const article = ref(null)
const loading = ref(false)
const error = ref(null)

watch(() => props.articleId, async (newId) => {
  if (newId && props.isOpen) {
    await loadArticle(newId)
  }
}, { immediate: true })

watch(() => props.isOpen, async (isOpen) => {
  if (isOpen && props.articleId) {
    await loadArticle(props.articleId)
  }
})

const loadArticle = async (id) => {
  loading.value = true
  error.value = null

  try {
    const response = await getArticle(id)
    article.value = response.data
  } catch (err) {
    error.value = 'Failed to load article details'
    console.error('Error loading article:', err)
  } finally {
    loading.value = false
  }
}

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.9);
}
</style>
