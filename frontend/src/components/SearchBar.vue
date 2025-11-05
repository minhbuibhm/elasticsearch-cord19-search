<template>
  <div class="w-full max-w-4xl">
    <div class="relative">
      <!-- Search Icon -->
      <div class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      <!-- Search Input -->
      <input
        v-model="localQuery"
        type="text"
        :placeholder="placeholder"
        class="w-full pl-14 pr-4 py-5 text-lg border-2 border-gray-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-primary-200 focus:border-primary-500 transition-all shadow-sm"
        @keyup.enter="handleSearch"
      />
    </div>

    <!-- Search Button -->
    <div class="mt-6 flex justify-center">
      <button
        @click="handleSearch"
        :disabled="!localQuery.trim()"
        class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
      >
        <svg class="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        DISCOVER
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  query: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Search research papers...'
  }
})

const emit = defineEmits(['search', 'update:query'])

const localQuery = ref(props.query)

watch(() => props.query, (newVal) => {
  localQuery.value = newVal
})

watch(localQuery, (newVal) => {
  emit('update:query', newVal)
})

const handleSearch = () => {
  if (localQuery.value.trim()) {
    emit('search', {
      query: localQuery.value.trim()
    })
  }
}
</script>
