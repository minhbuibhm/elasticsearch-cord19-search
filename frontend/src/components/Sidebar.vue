<template>
  <div class="w-20 bg-gradient-to-b from-primary-600 to-secondary-600 flex flex-col items-center py-8 shadow-lg">
    <!-- Logo / Brand -->
    <div class="mb-12">
      <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-md">
        <span class="text-2xl font-bold bg-gradient-to-r from-primary-500 to-secondary-500 bg-clip-text text-transparent">
          D
        </span>
      </div>
    </div>

    <!-- Navigation Icons -->
    <nav class="flex-1 flex flex-col space-y-6">
      <!-- Search -->
      <router-link
        to="/"
        class="nav-icon"
        :class="{ active: $route.name === 'search' }"
        title="Search"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </router-link>

      <!-- Bookmarks -->
      <router-link
        to="/bookmarks"
        class="nav-icon"
        :class="{ active: $route.name === 'bookmarks' }"
        title="Bookmarks"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
      </router-link>

      <!-- Documents / Reports (placeholder) -->
      <button
        class="nav-icon opacity-50 cursor-not-allowed"
        title="Reports (Coming Soon)"
        disabled
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </button>
    </nav>

    <!-- User Profile / Logout -->
    <div class="mt-auto">
      <button
        @click="handleLogout"
        class="nav-icon"
        title="Logout"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { useAuth } from '@/composables/useAuth'
import { useRouter } from 'vue-router'

const { logout } = useAuth()
const router = useRouter()

const handleLogout = () => {
  logout()
  router.push('/')
}
</script>

<style scoped>
.nav-icon {
  @apply w-14 h-14 flex items-center justify-center rounded-xl text-white/70 hover:text-white hover:bg-white/10 transition-all duration-200 cursor-pointer;
}

.nav-icon.active {
  @apply text-white bg-white/20 shadow-lg;
}
</style>
