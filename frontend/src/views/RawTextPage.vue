<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white shadow-sm sticky top-0 z-10">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        <button
          @click="goBack"
          class="flex items-center text-gray-600 hover:text-primary-600 transition-colors"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back
        </button>
        
        <!-- Source badge -->
        <span 
          v-if="content?.source_type"
          :class="[
            'px-3 py-1 rounded-full text-sm font-medium',
            content.source_type === 'pmc' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
          ]"
        >
          {{ content.source_type === 'pmc' ? 'PMC Source' : 'PDF Source' }}
        </span>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-16">
        <div class="inline-block animate-spin rounded-full h-16 w-16 border-4 border-primary-500 border-t-transparent"></div>
        <p class="mt-4 text-gray-600">Loading full text content...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-16">
        <svg class="w-20 h-20 mx-auto text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-red-600 font-medium text-lg">{{ error }}</p>
        <button @click="loadContent" class="mt-4 btn-primary">
          Try Again
        </button>
      </div>

      <!-- Content -->
      <div v-else-if="content" class="space-y-6">
        <!-- Header Card -->
        <div class="bg-white rounded-2xl shadow-md p-8">
          <!-- Title -->
          <h1 class="text-2xl font-bold text-gray-900 mb-4">
            {{ content.title || 'Untitled' }}
          </h1>
          
          <!-- Authors -->
          <div v-if="content.authors?.length > 0" class="mb-4">
            <div class="flex flex-wrap gap-2">
              <span 
                v-for="(author, index) in content.authors" 
                :key="index"
                class="inline-flex items-center px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-700"
              >
                <svg class="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                {{ author.name }}
              </span>
            </div>
          </div>

          <!-- Paper ID & Stats -->
          <div class="flex flex-wrap gap-4 text-sm text-gray-500">
            <span v-if="content.paper_id">
              <span class="font-medium">ID:</span> {{ content.paper_id }}
            </span>
            <span v-if="content.references_count">
              <span class="font-medium">References:</span> {{ content.references_count }}
            </span>
            <span v-if="content.sections?.length">
              <span class="font-medium">Sections:</span> {{ content.sections.length }}
            </span>
          </div>
        </div>

        <!-- Section Navigation -->
        <div v-if="content.sections?.length > 0" class="bg-white rounded-xl shadow-sm p-4">
          <h3 class="text-sm font-semibold text-gray-500 uppercase mb-2">Quick Navigation</h3>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="(section, index) in content.sections"
              :key="'nav-' + index"
              @click="scrollToSection(index)"
              class="px-3 py-1 text-sm bg-gray-100 hover:bg-primary-100 text-gray-700 hover:text-primary-700 rounded-lg transition-colors"
            >
              {{ section.title }}
            </button>
          </div>
        </div>

        <!-- Abstract -->
        <div v-if="content.abstract?.length > 0" class="bg-white rounded-2xl shadow-md p-8">
          <h2 class="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <svg class="w-6 h-6 mr-2 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Abstract
          </h2>
          <div class="space-y-3">
            <p 
              v-for="(para, index) in content.abstract" 
              :key="'abstract-' + index"
              class="text-gray-700 leading-relaxed"
            >
              {{ para.text }}
            </p>
          </div>
        </div>

        <!-- Body Sections -->
        <div 
          v-for="(section, sectionIndex) in content.sections" 
          :key="'section-' + sectionIndex"
          :ref="el => sectionRefs[sectionIndex] = el"
          class="bg-white rounded-2xl shadow-md p-8"
        >
          <h2 class="text-xl font-bold text-gray-900 mb-4">
            {{ section.title }}
          </h2>
          <div class="space-y-4">
            <p 
              v-for="(para, paraIndex) in section.paragraphs" 
              :key="'para-' + sectionIndex + '-' + paraIndex"
              class="text-gray-700 leading-relaxed"
            >
              {{ para.text }}
            </p>
          </div>
        </div>

        <!-- Tables -->
        <div v-if="content.tables?.length > 0" class="bg-white rounded-2xl shadow-md p-8">
          <h2 class="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <svg class="w-6 h-6 mr-2 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            Tables
          </h2>
          <div class="space-y-4">
            <div 
              v-for="(table, index) in content.tables" 
              :key="'table-' + index"
              class="p-4 bg-gray-50 rounded-lg border border-gray-200"
            >
              <p class="text-sm font-medium text-gray-500 mb-1">{{ table.id }}</p>
              <p class="text-gray-700">{{ table.caption }}</p>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!content.sections?.length && !content.abstract?.length" class="text-center py-8 text-gray-500">
          <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p class="text-lg">No content available for this document</p>
        </div>
      </div>

      <!-- No Path Provided -->
      <div v-else class="text-center py-16">
        <svg class="w-20 h-20 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-gray-600">No content path specified</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const content = ref(null)
const loading = ref(false)
const error = ref(null)
const sectionRefs = ref({})

const path = computed(() => route.query.path || '')

onMounted(() => {
  if (path.value) {
    loadContent()
  }
})

const loadContent = async () => {
  if (!path.value) return

  loading.value = true
  error.value = null

  try {
    const response = await axios.get('/api/raw-text', {
      params: { path: path.value }
    })
    content.value = response.data
  } catch (err) {
    console.error('Error loading raw text:', err)
    if (err.response?.status === 404) {
      error.value = 'Content not found. Please ensure the dataset is available.'
    } else if (err.response?.status === 400) {
      error.value = 'Invalid content path.'
    } else {
      error.value = 'Failed to load full text content'
    }
  } finally {
    loading.value = false
  }
}

const scrollToSection = (index) => {
  const element = sectionRefs.value[index]
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const goBack = () => {
  router.back()
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
