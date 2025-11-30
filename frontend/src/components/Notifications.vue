<template>
  <div class="notification-container">
    <transition-group name="notification" tag="div">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="[
          'notification',
          `notification-${notification.type}`,
          { 'notification-persistent': notification.persistent }
        ]"
        @click="removeNotification(notification.id)"
      >
        <div class="notification-icon">
          <v-icon :color="getIconColor(notification.type)">
            {{ getIcon(notification.type) }}
          </v-icon>
        </div>

        <div class="notification-content">
          <div class="notification-title" v-if="notification.title">
            {{ notification.title }}
          </div>
          <div class="notification-message">
            {{ notification.message }}
          </div>
          <div class="notification-details" v-if="notification.details">
            <v-expansion-panels variant="accordion" class="notification-details-panel">
              <v-expansion-panel>
                <v-expansion-panel-title class="notification-details-title">
                  <v-icon start size="16">mdi-information</v-icon>
                  Detail
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <pre class="notification-details-text">{{ notification.details }}</pre>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>
        </div>

        <div class="notification-actions">
          <v-btn
            v-if="notification.showProgress"
            icon
            size="small"
            variant="text"
            @click.stop="cancelNotification(notification.id)"
          >
            <v-icon size="16">mdi-close</v-icon>
          </v-btn>

          <v-btn
            v-else
            icon
            size="small"
            variant="text"
            @click.stop="removeNotification(notification.id)"
            class="notification-close"
          >
            <v-icon size="16">mdi-close</v-icon>
          </v-btn>
        </div>

        <div
          v-if="notification.showProgress"
          class="notification-progress"
        >
          <v-progress-linear
            :model-value="notification.progress || 0"
            :color="getProgressColor(notification.type)"
            height="3"
          />
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title?: string
  message: string
  details?: string
  timeout?: number
  persistent?: boolean
  showProgress?: boolean
  progress?: number
}

const notifications = ref<Notification[]>([])

const addNotification = (notification: Omit<Notification, 'id'>) => {
  const id = Date.now().toString() + Math.random().toString(36).substr(2, 9)
  const newNotification: Notification = {
    id,
    timeout: 5000,
    ...notification
  }

  notifications.value.push(newNotification)

  // Auto remove if not persistent and no progress
  if (!newNotification.persistent && !newNotification.showProgress && newNotification.timeout) {
    setTimeout(() => {
      removeNotification(id)
    }, newNotification.timeout)
  }

  return id
}

const removeNotification = (id: string) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

const cancelNotification = (id: string) => {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    notification.showProgress = false
    if (!notification.persistent) {
      setTimeout(() => {
        removeNotification(id)
      }, 2000)
    }
  }
}

const getIcon = (type: string) => {
  const icons = {
    success: 'mdi-check-circle',
    error: 'mdi-alert-circle',
    warning: 'mdi-alert',
    info: 'mdi-information'
  }
  return icons[type as keyof typeof icons] || 'mdi-information'
}

const getIconColor = (type: string) => {
  const colors = {
    success: 'success',
    error: 'error',
    warning: 'warning',
    info: 'info'
  }
  return colors[type as keyof typeof colors] || 'info'
}

const getProgressColor = (type: string) => {
  const colors = {
    success: 'success',
    error: 'error',
    warning: 'warning',
    info: 'info'
  }
  return colors[type as keyof typeof colors] || 'info'
}

// Helper functions for different notification types
const showSuccess = (message: string, options?: Partial<Notification>) => {
  return addNotification({
    type: 'success',
    message,
    ...options
  })
}

const showError = (message: string, options?: Partial<Notification>) => {
  return addNotification({
    type: 'error',
    message,
    timeout: 8000, // Longer timeout for errors
    persistent: true,
    ...options
  })
}

const showWarning = (message: string, options?: Partial<Notification>) => {
  return addNotification({
    type: 'warning',
    message,
    ...options
  })
}

const showInfo = (message: string, options?: Partial<Notification>) => {
  return addNotification({
    type: 'info',
    message,
    ...options
  })
}

const showProgress = (message: string, options?: Partial<Notification>) => {
  return addNotification({
    type: 'info',
    message,
    showProgress: true,
    persistent: true,
    progress: 0,
    ...options
  })
}

const updateProgress = (id: string, progress: number, message?: string) => {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    notification.progress = progress
    if (message) {
      notification.message = message
    }
  }
}

const completeProgress = (id: string, success: boolean = true, finalMessage?: string) => {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    notification.type = success ? 'success' : 'error'
    notification.showProgress = false
    notification.persistent = false
    notification.timeout = 3000
    if (finalMessage) {
      notification.message = finalMessage
    }

    setTimeout(() => {
      removeNotification(id)
    }, notification.timeout)
  }
}

// Expose functions globally
const exposeMethods = {
  showSuccess,
  showError,
  showWarning,
  showInfo,
  showProgress,
  updateProgress,
  completeProgress,
  addNotification,
  removeNotification
}

defineExpose(exposeMethods)

// Also attach to window for external access
if (typeof window !== 'undefined') {
  (window as any).__notificationMethods = exposeMethods
}
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  max-width: 400px;
  pointer-events: none;
}

.notification {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), 0.2);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  margin-bottom: 12px;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  pointer-events: all;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.notification:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
}

.notification-persistent {
  border-left: 4px solid rgb(var(--v-theme-warning));
}

.notification-success {
  border-left: 4px solid rgb(var(--v-theme-success));
}

.notification-error {
  border-left: 4px solid rgb(var(--v-theme-error));
}

.notification-warning {
  border-left: 4px solid rgb(var(--v-theme-warning));
}

.notification-info {
  border-left: 4px solid rgb(var(--v-theme-info));
}

.notification-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(var(--v-theme-surface-variant));
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 4px;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.3;
}

.notification-message {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.87);
  line-height: 1.4;
  word-break: break-word;
}

.notification-details {
  margin-top: 8px;
}

.notification-details-panel {
  background: transparent !important;
  box-shadow: none !important;
}

.notification-details-title {
  font-size: 0.75rem;
  font-weight: 500;
  min-height: 32px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.notification-details-text {
  font-size: 0.75rem;
  background: rgba(var(--v-theme-surface-variant));
  padding: 8px;
  border-radius: 6px;
  max-height: 150px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.3;
}

.notification-actions {
  flex-shrink: 0;
}

.notification-close {
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.notification-close:hover {
  opacity: 1;
}

.notification-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  border-radius: 0 0 12px 12px;
  overflow: hidden;
}

/* Animations */
.notification-enter-active {
  transition: all 0.3s ease;
}

.notification-leave-active {
  transition: all 0.2s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.notification-move {
  transition: transform 0.3s ease;
}

/* Responsive */
@media (max-width: 600px) {
  .notification-container {
    top: 10px;
    right: 10px;
    left: 10px;
    max-width: none;
  }

  .notification {
    padding: 12px;
  }

  .notification-title {
    font-size: 0.9rem;
  }

  .notification-message {
    font-size: 0.8rem;
  }
}
</style>