<template>
  <div class="flex h-screen overflow-hidden">
    <!-- Sidebar -->
    <Sidebar />

    <!-- Main Content Area -->
    <div class="flex-1 overflow-y-auto">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>

    <!-- Login Modal (shown if not authenticated) -->
    <div v-if="!isAuthenticated" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
        <div class="text-center mb-6">
          <h2 class="text-3xl font-bold bg-gradient-to-r from-primary-500 to-secondary-500 bg-clip-text text-transparent mb-2">
            Welcome to Paper-Finder
          </h2>
          <p class="text-gray-600">Enter your name to get started</p>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <input
              v-model="username"
              type="text"
              placeholder="Your name"
              class="input-field"
              required
              minlength="3"
            />
          </div>

          <button type="submit" class="w-full btn-primary">
            Enter
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import { useAuth } from '@/composables/useAuth'

const { isAuthenticated, login } = useAuth()
const username = ref('')

const handleLogin = async () => {
  if (username.value.trim().length >= 3) {
    await login(username.value.trim())
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
