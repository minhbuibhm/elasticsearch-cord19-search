<template>
  <div class="w-full max-w-4xl">
    <!-- Toggle Button -->
    <button
      @click="isExpanded = !isExpanded"
      class="flex items-center space-x-2 text-primary-600 hover:text-primary-700 font-medium mb-4"
    >
      <svg
        class="w-5 h-5 transform transition-transform"
        :class="{ 'rotate-180': isExpanded }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
      <span>Advanced Search</span>
    </button>

    <!-- Filters Panel -->
    <transition name="slide">
      <div v-if="isExpanded" class="bg-white rounded-xl shadow-md p-6 space-y-4">
        <!-- Time Range -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Publication Date
            </label>
            <select
              v-model="filters.time_range.type"
              class="input-field"
              @change="handleTimeTypeChange"
            >
              <option value="any">Any time</option>
              <option value="since">Since year</option>
              <option value="range">Custom range</option>
            </select>
          </div>

          <!-- Since Year -->
          <div v-if="filters.time_range.type === 'since'">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Since
            </label>
            <select v-model="filters.time_range.value" class="input-field">
              <option value="2025">Since 2025</option>
              <option value="2024">Since 2024</option>
              <option value="2021">Since 2021</option>
              <option value="2020">Since 2020</option>
            </select>
          </div>
        </div>

        <!-- Custom Date Range -->
        <div v-if="filters.time_range.type === 'range'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              From
            </label>
            <input
              v-model="filters.time_range.start"
              type="date"
              class="input-field"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              To
            </label>
            <input
              v-model="filters.time_range.end"
              type="date"
              class="input-field"
            />
          </div>
        </div>

        <!-- Sort By and Article Type -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Sort by
            </label>
            <select v-model="filters.sort_by" class="input-field">
              <option value="relevance">Relevance</option>
              <option value="date">Date (newest first)</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Article Type
            </label>
            <select v-model="filters.article_type" class="input-field">
              <option value="any">Any type</option>
              <option value="review">Review articles</option>
            </select>
          </div>
        </div>

        <!-- Checkboxes -->
        <div class="flex flex-wrap gap-4">
          <div class="flex items-center">
            <input
              v-model="filters.include_patents"
              type="checkbox"
              id="include-patents"
              class="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
            />
            <label for="include-patents" class="ml-2 text-sm text-gray-700 cursor-pointer">
              Include patents
            </label>
          </div>

          <div class="flex items-center">
            <input
              v-model="filters.include_citations"
              type="checkbox"
              id="include-citations"
              class="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
            />
            <label for="include-citations" class="ml-2 text-sm text-gray-700 cursor-pointer">
              Include citations
            </label>
          </div>
        </div>

        <!-- Apply Button -->
        <div class="flex justify-end pt-2">
          <button
            @click="applyFilters"
            class="btn-secondary"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const emit = defineEmits(['update'])

const isExpanded = ref(false)

const filters = reactive({
  time_range: {
    type: 'any',
    value: null,
    start: null,
    end: null
  },
  sort_by: 'relevance',
  article_type: 'any',
  include_patents: false,
  include_citations: true
})

const handleTimeTypeChange = () => {
  if (filters.time_range.type === 'any') {
    filters.time_range.value = null
    filters.time_range.start = null
    filters.time_range.end = null
  } else if (filters.time_range.type === 'since') {
    filters.time_range.value = '2024'
    filters.time_range.start = null
    filters.time_range.end = null
  } else if (filters.time_range.type === 'range') {
    filters.time_range.value = null
  }
}

const applyFilters = () => {
  emit('update', { ...filters })
}

// Auto-emit on changes (for real-time filtering)
watch(filters, () => {
  emit('update', { ...filters })
}, { deep: true })
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  max-height: 500px;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
