import { App, ref } from 'vue'

interface NotificationOptions {
  title?: string
  details?: string
  timeout?: number
  persistent?: boolean
  showProgress?: boolean
  progress?: number
}

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $notify: {
      success: (message: string, options?: NotificationOptions) => string
      error: (message: string, options?: NotificationOptions) => string
      warning: (message: string, options?: NotificationOptions) => string
      info: (message: string, options?: NotificationOptions) => string
      progress: (message: string, options?: NotificationOptions) => string
      updateProgress: (id: string, progress: number, message?: string) => void
      completeProgress: (id: string, success?: boolean, message?: string) => void
    }
  }
}

// Simple notification store using native browser notifications + console
const NotificationsPlugin = {
  install(app: App) {
    const activeNotifications = new Map<string, any>()

    const notify = {
      success: (message: string, options?: NotificationOptions) => {
        const id = 'notif-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9)
        console.log('✅ SUCCESS:', options?.title || message, message, options?.details || '')

        // Browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
          const notification = new Notification(options?.title || 'Success', {
            body: message,
            icon: '/favicon.ico',
            tag: id
          })

          if (!options?.persistent && options?.timeout) {
            setTimeout(() => notification.close(), options.timeout)
          }
        }

        activeNotifications.set(id, { type: 'success', message, options })
        return id
      },
      error: (message: string, options?: NotificationOptions) => {
        const id = 'notif-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9)
        console.error('❌ ERROR:', options?.title || message, message, options?.details || '')

        // Browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
          const notification = new Notification(options?.title || 'Error', {
            body: message,
            icon: '/favicon.ico',
            tag: id
          })

          if (!options?.persistent && options?.timeout) {
            setTimeout(() => notification.close(), options.timeout)
          }
        }

        activeNotifications.set(id, { type: 'error', message, options })
        return id
      },
      warning: (message: string, options?: NotificationOptions) => {
        const id = 'notif-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9)
        console.warn('⚠️ WARNING:', options?.title || message, message, options?.details || '')

        // Browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
          const notification = new Notification(options?.title || 'Warning', {
            body: message,
            icon: '/favicon.ico',
            tag: id
          })

          if (!options?.persistent && options?.timeout) {
            setTimeout(() => notification.close(), options.timeout)
          }
        }

        activeNotifications.set(id, { type: 'warning', message, options })
        return id
      },
      info: (message: string, options?: NotificationOptions) => {
        const id = 'notif-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9)
        console.info('ℹ️ INFO:', options?.title || message, message, options?.details || '')

        // Browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
          const notification = new Notification(options?.title || 'Info', {
            body: message,
            icon: '/favicon.ico',
            tag: id
          })

          if (!options?.persistent && options?.timeout) {
            setTimeout(() => notification.close(), options.timeout)
          }
        }

        activeNotifications.set(id, { type: 'info', message, options })
        return id
      },
      progress: (message: string, options?: NotificationOptions) => {
        const id = 'notif-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9)
        console.log('🔄 PROGRESS:', options?.title || message, message, `Progress: ${options?.progress || 0}%`)

        activeNotifications.set(id, { type: 'info', message, options, showProgress: true })
        return id
      },
      updateProgress: (id: string, progress: number, message?: string) => {
        const notification = activeNotifications.get(id)
        if (notification) {
          notification.options = { ...notification.options, progress }
          console.log(`🔄 PROGRESS UPDATE (${id}): ${progress}% ${message ? '- ' + message : ''}`)
        }
      },
      completeProgress: (id: string, success: boolean = true, message?: string) => {
        const notification = activeNotifications.get(id)
        if (notification) {
          const status = success ? '✅ COMPLETED' : '❌ FAILED'
          console.log(`${status} (${id}): ${message || notification.message}`)

          if ('Notification' in window && Notification.permission === 'granted') {
            const browserNotif = new Notification(
              success ? (notification.options?.title || 'Success') : (notification.options?.title || 'Error'),
              {
                body: message || notification.message,
                icon: '/favicon.ico',
                tag: id + '-completed'
              }
            )

            setTimeout(() => browserNotif.close(), 3000)
          }

          activeNotifications.delete(id)
        }
      }
    }

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }

    // Make it globally available
    app.config.globalProperties.$notify = notify

    // Also provide it for composition API
    app.provide('notify', notify)

    // Store for window access
    if (typeof window !== 'undefined') {
      (window as any).__notificationMethods = notify
    }
  }
}

export default NotificationsPlugin