<template>
  <div class="min-h-screen flex flex-col items-center justify-center px-4 bg-gradient-to-br from-primary-50 via-white to-secondary-50">
    <!-- Hero Section -->
    <div class="text-center mb-12 animate-fade-in">
      <h1 class="text-6xl font-bold mb-4">
        <span class="bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
          PAPER FINDER
        </span>
      </h1>
      <p class="text-xl text-gray-600 max-w-2xl mx-auto">
        Discover and explore research papers with AI-powered search
      </p>
      <p class="text-sm text-gray-500 mt-2">
        Powered by AI-driven semantic search across thousands of research papers
      </p>
    </div>

    <!-- Search Section -->
    <div class="w-full max-w-4xl space-y-6 animate-slide-up">
      <SearchBar
        v-model:query="searchQuery"
        @search="handleSearch"
      />

      <AdvancedFilters @update="handleFiltersUpdate" />
    </div>

    <!-- Stats Section -->
    <div class="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-3xl w-full">
      <div class="text-center animate-fade-in" style="animation-delay: 0.1s">
        <div class="text-4xl font-bold text-primary-600 mb-2">10+</div>
        <div class="text-gray-600">Research Papers</div>
      </div>
      <div class="text-center animate-fade-in" style="animation-delay: 0.2s">
        <div class="text-4xl font-bold text-secondary-600 mb-2">AI</div>
        <div class="text-gray-600">Semantic Search</div>
      </div>
      <div class="text-center animate-fade-in" style="animation-delay: 0.3s">
        <div class="text-4xl font-bold text-primary-600 mb-2">Fast</div>
        <div class="text-gray-600">Discovery</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import SearchBar from '@/components/SearchBar.vue'
import AdvancedFilters from '@/components/AdvancedFilters.vue'

const router = useRouter()
const searchQuery = ref('')
const advancedFilters = ref({})

const handleSearch = ({ query }) => {
  if (query.trim()) {
    router.push({
      name: 'results',
      query: {
        q: query
      }
    })
  }
}

const handleFiltersUpdate = (filters) => {
  advancedFilters.value = filters
}
</script>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.6s ease-out forwards;
}

.animate-slide-up {
  animation: slide-up 0.8s ease-out forwards;
}
</style>
