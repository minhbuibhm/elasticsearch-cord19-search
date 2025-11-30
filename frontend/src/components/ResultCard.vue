<template>
  <div
    class="card p-6 cursor-pointer hover:border-2 hover:border-primary-200 transition-all"
    @click="$emit('click')"
  >
    <div class="flex items-start justify-between mb-3">
      <!-- Similarity Score Badge -->
      <div v-if="article.similarity_score != null" class="badge-score">
        {{ article.similarity_score.toFixed(2) }}
      </div>
      <div v-else class="h-6"></div> <!-- Spacer when no score -->

      <!-- Action Icons -->
      <div class="flex items-center space-x-2">
        <!-- Bookmark Icon -->
        <button
          @click.stop="toggleBookmark"
          class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          :class="{ 'text-yellow-500': isBookmarked, 'text-gray-400': !isBookmarked }"
          :title="isBookmarked ? 'Remove bookmark' : 'Bookmark article'"
        >
          <svg
            class="w-5 h-5"
            :fill="isBookmarked ? 'currentColor' : 'none'"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </button>

        <!-- Open in New Tab Icon -->
        <a
          v-if="article.full_text_url"
          :href="article.full_text_url"
          target="_blank"
          @click.stop
          class="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-primary-600 transition-colors"
          title="Open in new tab"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </div>

    <!-- Title -->
    <h3 class="text-xl font-bold text-gray-900 mb-2 hover:text-primary-600 transition-colors">
      {{ article.title }}
    </h3>

    <!-- Meta Information -->
    <div class="flex flex-wrap items-center gap-3 text-sm text-gray-600 mb-3">
      <!-- Authors -->
      <div class="flex items-center">
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <span>{{ formatAuthors(article.authors) }}</span>
      </div>

      <!-- Journal -->
      <div v-if="article.journal" class="flex items-center">
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        <span>{{ article.journal }}</span>
      </div>

      <!-- Publication Date -->
      <div v-if="article.publication_date" class="flex items-center">
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span>{{ formatDate(article.publication_date) }}</span>
      </div>
    </div>

    <!-- Abstract Snippet -->
    <p class="text-gray-700 leading-relaxed mb-2">
      {{ article.abstract_snippet }}
    </p>

    <!-- Show More Link -->
    <button
      class="text-primary-600 hover:text-primary-700 font-medium text-sm"
      @click.stop="$emit('click')"
    >
      Show more →
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useBookmarkApi } from '@/composables/useApi'

const props = defineProps({
  article: {
    type: Object,
    required: true
  },
  bookmarked: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'bookmark-toggle'])

const { addBookmark, removeBookmark } = useBookmarkApi()
const isBookmarked = ref(props.bookmarked)

const toggleBookmark = async () => {
  try {
    if (isBookmarked.value) {
      await removeBookmark(props.article.id)
      isBookmarked.value = false
    } else {
      await addBookmark(props.article.id)
      isBookmarked.value = true
    }
    emit('bookmark-toggle', props.article.id, isBookmarked.value)
  } catch (error) {
    console.error('Error toggling bookmark:', error)
  }
}

const formatAuthors = (authors) => {
  if (!authors || authors.length === 0) return 'Unknown'
  if (authors.length === 1) return authors[0]
  if (authors.length === 2) return authors.join(' & ')
  return `${authors[0]} et al.`
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>
