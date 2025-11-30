<template>
  <v-container fluid class="fill-height">
    <v-row justify="center" align="center" class="pa-4">
      <v-col cols="12" md="8" lg="6" xl="4">
        <!-- Main 404 Card -->
        <v-card
          class="elevation-12 rounded-xl"
          :class="isDark ? 'bg-gray-900' : 'bg-white'"
        >
          <v-card-text class="pa-8 text-center">
            <!-- 404 Icon -->
            <div class="mb-6">
              <v-icon
                size="120"
                :color="isDark ? 'blue-grey-lighten-1' : 'grey-lighten-1'"
                class="mb-4"
              >
                mdi-alert-circle-outline
              </v-icon>
            </div>

            <!-- Error Code -->
            <h1
              class="text-h2 font-weight-bold mb-2"
              :class="isDark ? 'text-blue-grey-lighten-1' : 'text-grey-lighten-1'"
            >
              404
            </h1>

            <!-- Error Message -->
            <h2 class="text-h5 font-weight-medium mb-2">
              Halaman Tidak Ditemukan
            </h2>

            <p class="text-body-1 text-medium-emphasis mb-6">
              Maaf, halaman yang Anda cari tidak ada atau telah dipindahkan.
              URL yang Anda masukkan mungkin salah.
            </p>

            <!-- Action -->
            <div class="d-flex justify-center">
              <!-- Report Issue -->
              <v-btn
                color="primary"
                size="large"
                prepend-icon="mdi-bug-outline"
                class="text-none"
                @click="reportIssue"
              >
                Laporkan Masalah
              </v-btn>
            </div>

            <!-- Additional Info -->
            <v-divider class="my-6"></v-divider>

            <div class="text-caption text-medium-emphasis">
              <div class="mb-2">
                <strong>URL yang diakses:</strong> {{ currentPath }}
              </div>
              <div class="mb-2">
                <strong>Waktu:</strong> {{ currentTime }}
              </div>
              <div>
                <strong>ID Referensi:</strong> {{ referenceId }}
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- Contact Support -->
        <v-card
          class="mt-4 rounded-xl elevation-2"
          :color="isDark ? 'blue-darken-3' : 'info'"
          variant="elevated"
        >
          <v-card-text class="pa-4 text-center">
            <v-icon class="mr-2" size="large">mdi-headset</v-icon>
            <div class="font-weight-medium">
              Butuh bantuan? Hubungi IT Support
            </div>
            <div class="text-caption mt-1">
              📧 support@ajnusa.com | 📧 ahmad@ajnusa.com
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Report Issue Dialog -->
    <v-dialog v-model="showReportDialog" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-bug</v-icon>
          Laporkan Masalah
        </v-card-title>

        <v-card-text>
          <v-textarea
            v-model="issueReport"
            label="Deskripsi Masalah"
            placeholder="Jelaskan masalah yang Anda alami..."
            rows="4"
            auto-grow
            variant="outlined"
          ></v-textarea>

          <v-checkbox
            v-model="includeScreenshot"
            label="Sertakan screenshot halaman"
            hide-details
          ></v-checkbox>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showReportDialog = false">
            Batal
          </v-btn>
          <v-btn color="primary" @click="submitReport">
            Kirim Laporan
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getEncryptedToken } from '@/utils/crypto'
import { useTheme } from 'vuetify'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const theme = useTheme()

// Computed for theme detection
const isDark = computed(() => theme.global.name.value === 'dark')

// State
const showReportDialog = ref(false)
const issueReport = ref('')
const includeScreenshot = ref(false)
const referenceId = ref('')

// Computed
const isAuthenticated = computed(() => {
  return !!getEncryptedToken('access_token')
})

const currentPath = computed(() => route.fullPath)
const currentTime = computed(() => {
  return new Date().toLocaleString('id-ID', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Jakarta'
  })
})

// Methods
const reportIssue = () => {
  showReportDialog.value = true
}

const submitReport = async () => {
  try {
    const reportData = {
      issue: issueReport.value,
      path: currentPath.value,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      referenceId: referenceId.value,
      includeScreenshot: includeScreenshot.value
    }

    // Send report to backend
    await fetch('/api/error-report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(reportData)
    })

    // Show success message
    alert('Terima kasih! Laporan Anda telah dikirim ke tim IT Support.')
    showReportDialog.value = false
    issueReport.value = ''
    includeScreenshot.value = false
  } catch (error) {
    console.error('Failed to submit report:', error)
    alert('Maaf, gagal mengirim laporan. Silakan hubungi IT Support langsung.')
  }
}

// Generate reference ID on mount
onMounted(() => {
  referenceId.value = 'ERR-' + Date.now().toString(36).toUpperCase()

  // Log 404 error for analytics
  console.warn(`404 Error - Reference: ${referenceId.value} - Path: ${currentPath.value}`)

  // Optional: Send to analytics service
  if (typeof (window as any).gtag !== 'undefined') {
    (window as any).gtag('event', '404_error', {
      page_path: currentPath.value,
      reference_id: referenceId.value
    })
  }
})
</script>

<style scoped>
.v-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* Custom animations */
@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}

.v-icon[size="120"] {
  animation: float 3s ease-in-out infinite;
}

/* Dark theme adjustments */
.v-theme--dark .v-container {
  background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%);
}
</style>