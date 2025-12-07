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
        <!-- Search Method and Tokenizer -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Search Method
            </label>
            <select v-model="filters.search_method" class="input-field">
              <option value="regular">Regular Search</option>
              <option value="semantic">Semantic Search (AI-powered)</option>
              <option value="hybrid">Hybrid Search (Keyword + AI)</option>
            </select>
          </div>

          <!-- Tokenizer (only for regular search) -->
          <div v-if="filters.search_method === 'regular'">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Tokenizer
            </label>
            <select v-model="filters.tokenizer" class="input-field">
              <option value="Standard">Standard</option>
              <option value="N-Gram">N-Gram (partial matching)</option>
            </select>
          </div>
        </div>

        <!-- Year Filter -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Publication Year
            </label>
            <select v-model="filters.year" class="input-field">
              <option :value="null">Any year</option>
              <option value="2025">2025</option>
              <option value="2024">2024</option>
              <option value="2023">2023</option>
              <option value="2022">2022</option>
              <option value="2021">2021</option>
              <option value="2020">2020</option>
              <option value="2019">2019</option>
              <option value="2018">2018</option>
            </select>
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
  search_method: 'regular',
  tokenizer: 'Standard',
  year: null
})

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
