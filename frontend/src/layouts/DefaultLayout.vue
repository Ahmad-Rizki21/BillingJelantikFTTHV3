<template>
 <v-app class="modern-app">
    <v-system-bar 
     v-if="settingsStore.maintenanceMode.isActive"
      color="warning" 
      window 
      class="maintenance-banner" 
      >
      <v-icon class="me-2">mdi-alert</v-icon>
      <span>{{ settingsStore.maintenanceMode.message }}</span>
    </v-system-bar>
    <v-navigation-drawer
      v-model="drawer"
      :rail="rail && !isMobile"
      :temporary="isMobile"
      :permanent="!isMobile"
      class="modern-drawer"
      :width="isMobile ? '280' : '280'"
    >
      <v-list-item class="sidebar-header" :class="{'px-0': rail && !isMobile}" :ripple="false">
        <div class="header-flex-container">
          <img v-if="!rail || isMobile" :src="logoSrc" alt="Jelantik Logo" class="sidebar-logo-full"/>
          
          <v-icon v-if="rail && !isMobile" color="primary" size="large">mdi-alpha-j</v-icon>

          <div v-if="!rail || isMobile" class="sidebar-title-wrapper">
            <h1 class="sidebar-title">Artacom Ftth</h1>
            <span class="sidebar-subtitle">PORTAL CUSTOMER V2.5</span>
          </div>

          <v-spacer v-if="!rail || isMobile"></v-spacer>

          <v-btn
            v-if="!isMobile"
            icon="mdi-chevron-left"
            variant="text"
            size="small"
            @click.stop="rail = !rail"
          ></v-btn>
          
          <v-btn
            v-if="isMobile"
            icon="mdi-close"
            variant="text"
            size="small"
            @click.stop="drawer = false"
          ></v-btn>
        </div>
      </v-list-item>

      <v-divider></v-divider>

      <div class="navigation-wrapper">
  <v-list nav class="navigation-menu">
    <template v-for="group in filteredMenuGroups" :key="group.title">
      <v-list-subheader v-if="!rail || isMobile" class="menu-subheader">{{ group.title }}</v-list-subheader>
      
      <template v-for="item in group.items" :key="item.title">
        <v-list-group 
          v-if="'children' in item"
          :value="item.value"
        >
          <template v-slot:activator="{ props }">
            <v-list-item
              v-bind="props"
              :prepend-icon="item.icon"
              :title="item.title"
              class="nav-item"
            ></v-list-item>
          </template>

              <v-list-item
          v-for="subItem in item.children"
          :key="subItem.title"
          :title="subItem.title"
          :to="subItem.to"
          :prepend-icon="subItem.icon"
          class="nav-sub-item"
      ></v-list-item>
        </v-list-group>
        
        <v-list-item
          v-else
          :prepend-icon="item.icon"
          :title="item.title"
          :value="item.value"
          :to="item.to"
          class="nav-item"
        >
          <template v-slot:append>
            <v-tooltip location="end">
              <template v-slot:activator="{ props }">
                <v-badge
                  v-if="item.value === 'langganan' && suspendedCount > 0"
                  color="error"
                  :content="suspendedCount"
                  inline
                  v-bind="props"
                ></v-badge>
              </template>
              <span>{{ suspendedCount }} langganan berstatus "Suspended"</span>
            </v-tooltip>
            <v-tooltip location="end">
            <template v-slot:activator="{ props }">
              <v-badge
                v-if="item.value === 'langganan' && stoppedCount > 0"
                color="grey"
                :content="stoppedCount"
                inline
                class="ms-2"
                v-bind="props"
              ></v-badge>
            </template>
            <span>{{ stoppedCount }} langganan berstatus "Berhenti"</span>
          </v-tooltip>
          <v-tooltip location="end">
            <template v-slot:activator="{ props }">
              <v-badge
                v-if="item.value === 'invoices' && unpaidInvoiceCount > 0"
                color="warning"
                :content="unpaidInvoiceCount"
                inline
                v-bind="props"
              ></v-badge>
            </template>
            <span>{{ unpaidInvoiceCount }} invoice belum dibayar</span>
          </v-tooltip>
          </template>
        </v-list-item>
      </template>
    </template>
  </v-list>
</div>

      <template v-slot:append>
        <div class="logout-section pa-4">
          <v-btn
            :block="!rail || isMobile"
            variant="tonal"
            color="grey-darken-1"
            class="logout-btn"
            :icon="rail && !isMobile"
            @click="handleLogout"
          >
            <v-icon v-if="rail && !isMobile">mdi-logout</v-icon>
            <span v-if="!rail || isMobile" class="d-flex align-center"><v-icon left>mdi-logout</v-icon>Logout</span>
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>

    <v-app-bar elevation="0" class="modern-app-bar">
      <v-btn
        icon="mdi-menu"
        variant="text"
        @click.stop="toggleDrawer"
      ></v-btn>
      <v-spacer></v-spacer>
      
      <v-btn icon variant="text" @click="toggleTheme" class="header-action-btn theme-toggle-btn">
        <v-icon>{{ theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>

      <v-menu offset-y>
        <template v-slot:activator="{ props }">
          <v-btn icon variant="text" class="header-action-btn" v-bind="props">
            <v-badge :content="notifications.length" color="error" :model-value="notifications.length > 0">
              <v-icon>mdi-bell-outline</v-icon>
            </v-badge>
          </v-btn>
        </template>
        <v-list class="pa-0" :width="isMobile ? '90vw' : '300'">
          <v-list-item class="font-weight-bold bg-grey-lighten-4">
              Notifikasi
              <template v-slot:append v-if="notifications.length > 0">
                  <v-btn variant="text" size="small" @click="markAllAsRead">Bersihkan</v-btn>
              </template>
          </v-list-item>
          <v-divider></v-divider>
          <div v-if="notifications.length === 0" class="text-center text-medium-emphasis pa-4">
              Tidak ada notifikasi baru.
          </div>
          <template v-else>
            <v-list-item
            v-for="(notif, index) in notifications"
            :key="index"
            class="py-2 notification-item"
            @click="handleNotificationClick(notif)"
              >
              <template v-slot:prepend>
                <v-avatar :color="getNotificationColor(notif.type)" size="32" class="me-3">
                    <v-icon size="18">{{ getNotificationIcon(notif.type) }}</v-icon>
                </v-avatar>
              </template>

              <div v-if="notif.type === 'new_payment'" class="notification-content">
                <v-list-item-title class="font-weight-medium text-body-2">Pembayaran Diterima</v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  <strong>{{ notif.data?.invoice_number || 'N/A' }}</strong> dari <strong>{{ notif.data?.pelanggan_nama || 'N/A' }}</strong> telah lunas.
                </v-list-item-subtitle>
              </div>

              <div v-else-if="notif.type === 'new_customer_for_noc'" class="notification-content">
                <v-list-item-title class="font-weight-medium text-body-2">Pelanggan Baru</v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  <strong>{{ notif.data?.pelanggan_nama || 'N/A' }}</strong> perlu dibuatkan Data Teknis.
                </v-list-item-subtitle>
              </div>

              <div v-else-if="notif.type === 'new_technical_data'" class="notification-content">
                <v-list-item-title class="font-weight-medium text-body-2">Data Teknis Baru</v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  Data teknis untuk <strong>{{ notif.data?.pelanggan_nama || 'N/A' }}</strong> telah ditambahkan.
                </v-list-item-subtitle>
              </div>

              <div v-else class="notification-content">
                <v-list-item-title class="font-weight-medium text-body-2">Notifikasi</v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  {{ notif.message || 'Anda memiliki notifikasi baru' }}
                </v-list-item-subtitle>
              </div>
            </v-list-item>
          </template>
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-main class="modern-main">
      <router-view></router-view>
    </v-main>
    
    <v-footer app height="69px" class="d-flex align-center justify-center text-medium-emphasis footer-responsive" style="border-top: 1px solid rgba(0,0,0,0.08);">
      <div class="footer-content">
        &copy; {{ new Date().getFullYear() }} <strong>Artacom Billing System</strong>. All Rights Design Reserved by 
        <a 
          href="https://www.instagram.com/amad.dyk/" 
          target="_blank" 
          rel="noopener noreferrer"
          class="text-decoration-none text-primary"
        >
          amad.dyk
        </a>
      </div>
    </v-footer>

  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useTheme } from 'vuetify'
import { useDisplay } from 'vuetify'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import apiClient from '@/services/api';
import logo from '@/assets/Jelantik 1.svg'; // Assuming you have a logo file

// --- State ---
const theme = useTheme();
const { mobile } = useDisplay();
const drawer = ref(true);
const rail = ref(false);
const router = useRouter();

// PERBAIKAN: Inisialisasi notifications dengan validasi lebih baik
const notifications = ref<any[]>([]);
// PERBAIKAN: Tambahkan watcher untuk memastikan notifications tetap array
watch(notifications, (newVal) => {
  if (!newVal || !Array.isArray(newVal)) {
    console.warn('[State] notifications bukan array, reset ke array kosong');
    notifications.value = [];
  }
}, { deep: true });

const suspendedCount = ref(0);
const unpaidInvoiceCount = ref(0);
const stoppedCount = ref(0);
const userCount = ref(0);
const roleCount = ref(0);
const userPermissions = ref<string[]>([]);
const authStore = useAuthStore();
let socket: WebSocket | null = null;

// Computed untuk mobile detection
const isMobile = computed(() => mobile.value);
const logoSrc = computed(() => theme.global.current.value.dark ? logo : logo);
const settingsStore = useSettingsStore();

// Toggle drawer function untuk mobile/desktop
function toggleDrawer() {
  if (isMobile.value) {
    drawer.value = !drawer.value;
  } else {
    rail.value = !rail.value;
  }
}

async function fetchSidebarBadges() {
  try {
    const response = await apiClient.get('/dashboard/sidebar-badges');
    suspendedCount.value = response.data.suspended_count;
    unpaidInvoiceCount.value = response.data.unpaid_invoice_count;
    stoppedCount.value = response.data.stopped_count; // <-- Ambil data baru
  } catch (error) {
    console.error("Gagal mengambil data badge sidebar:", error);
  }
}

let pingInterval: NodeJS.Timeout | null = null;
let reconnectTimeout: NodeJS.Timeout | null = null;
let notificationCleanupInterval: NodeJS.Timeout | null = null;
let tokenCheckInterval: NodeJS.Timeout | null = null;

function playSound(type: string) {
  try {
    console.log(`[Audio] Attempting to play sound for type: ${type}`);
    
    // PERBAIKAN: Mapping tipe notifikasi ke file audio dengan lebih baik
    let audioFile = '';
    switch (type) {
      case 'new_payment':
        audioFile = '/pembayaran.mp3';
        break;
      case 'new_customer_for_noc':
      case 'new_customer':
        audioFile = '/payment.mp3';
        break;
      case 'new_technical_data':
        audioFile = '/noc_finance.mp3';
        break;
      default:
        // Fallback untuk tipe tidak dikenal
        audioFile = '/notification.mp3';
        console.warn(`[Audio] Unknown notification type: ${type}, using fallback audio`);
    }

    // PERBAIKAN: Validasi file audio dengan lebih baik
    if (audioFile) {
      console.log(`[Audio] Loading audio file: ${audioFile}`);
      
      // PERBAIKAN: Cek apakah file audio benar-benar ada
      const audio = new Audio(audioFile);
      
      // PERBAIKAN: Tambahkan event listener untuk semua event audio
      audio.addEventListener('loadstart', () => {
        console.log(`[Audio] Loading started for ${audioFile}`);
      });
      
      audio.addEventListener('loadeddata', () => {
        console.log(`[Audio] Audio data loaded for ${audioFile}`);
      });
      
      audio.addEventListener('canplay', () => {
        console.log(`[Audio] Audio can play for ${audioFile}`);
      });
      
      audio.addEventListener('error', (e) => {
        console.error(`[Audio] Gagal memuat audio (${audioFile}):`, e);
        console.error(`[Audio] Error code: ${audio.error?.code}, message: ${audio.error?.message}`);
        // PERBAIKAN: Fallback ke beep sederhana
        fallbackBeep();
      });
      
      audio.addEventListener('play', () => {
        console.log(`[Audio] Playing audio: ${audioFile}`);
      });
      
      audio.addEventListener('ended', () => {
        console.log(`[Audio] Finished playing audio: ${audioFile}`);
      });
      
      // PERBAIKAN: Tambahkan timeout untuk playback
      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise.then(() => {
          console.log(`[Audio] Playback started successfully for ${audioFile}`);
        }).catch(error => {
          console.warn(`[Audio] Gagal memutar audio (${audioFile}):`, error);
          // PERBAIKAN: Fallback ke beep sederhana jika playback gagal
          fallbackBeep();
        });
      } else {
        console.warn(`[Audio] Play promise undefined for ${audioFile}`);
        // PERBAIKAN: Fallback ke beep sederhana jika playback gagal
        fallbackBeep();
      }
    } else {
      console.warn(`[Audio] Tidak ada file audio untuk type: ${type}`);
      // PERBAIKAN: Fallback ke beep sederhana jika tidak ada file
      fallbackBeep();
    }
  } catch (error) {
    console.error('[Audio] Gagal membuat/memutar audio:', error);
    // PERBAIKAN: Fallback ke beep sederhana jika terjadi error
    fallbackBeep();
  }
}

// PERBAIKAN: Fungsi fallback beep sederhana dengan logging yang lebih baik
function fallbackBeep() {
  try {
    console.log('[Audio] Fallback beep activated');
    
    // Metode 1: AudioContext (modern)
    const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
    if (AudioContext) {
      const context = new AudioContext();
      const oscillator = context.createOscillator();
      const gainNode = context.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(context.destination);
      
      oscillator.frequency.value = 800;
      oscillator.type = 'sine';
      gainNode.gain.setValueAtTime(0.3, context.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.5);
      
      oscillator.start(context.currentTime);
      oscillator.stop(context.currentTime + 0.5);
      
      console.log('[Audio] Fallback beep played using AudioContext');
      return;
    }
  } catch (error) {
    console.warn('[Audio] AudioContext fallback failed:', error);
  }
  
  try {
    // Metode 2: Fallback ke beep sederhana
    const context = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(context.destination);
    
    oscillator.frequency.value = 1000;
    oscillator.type = 'square';
    gainNode.gain.setValueAtTime(0.3, context.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.3);
    
    oscillator.start(context.currentTime);
    oscillator.stop(context.currentTime + 0.3);
    
    console.log('[Audio] Fallback beep played (square wave)');
  } catch (fallbackError) {
    console.warn('[Audio] All fallback methods failed:', fallbackError);
    
    // Metode 3: Alert sebagai fallback terakhir
    try {
      // Flash title bar
      let originalTitle = document.title;
      let flashInterval: NodeJS.Timeout | null = setInterval(() => {
        document.title = document.title === originalTitle ? "🔔 NOTIFIKASI BARU!" : originalTitle;
      }, 500);

      // Hentikan flashing setelah 3 detik
      setTimeout(() => {
        clearInterval(flashInterval);
        document.title = originalTitle;
      }, 3000);
      
      console.log('[Audio] Visual notification shown (Title flash)');
    } catch (visualError) {
      console.error('[Audio] All audio/visual methods failed:', visualError);
    }
  }
}

async function refreshTokenAndReconnect() {
  try {
    console.log('[WebSocket] Attempting to refresh token...');
    const success = await authStore.refreshToken();
    if (success) {
      console.log('[WebSocket] Token refreshed, reconnecting...');
      connectWebSocket();
    } else {
      console.log('[WebSocket] Token refresh failed, logging out...');
      authStore.logout();
    }
  } catch (error) {
    console.error('[WebSocket] Token refresh error:', error);
    authStore.logout();
  }
}

function connectWebSocket() {
  // 1. Hentikan jika sudah ada koneksi atau tidak ada token
  if (!authStore.token || (socket && socket.readyState === WebSocket.OPEN)) {
    return;
  }
  
  // Hentikan timer reconnect yang mungkin sedang berjalan
  if (reconnectTimeout) clearTimeout(reconnectTimeout);
  
  const token = authStore.token;
  const hostname = window.location.hostname;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  let wsUrl = '';

  // 2. Tentukan URL berdasarkan lingkungan (produksi atau development)
  if (hostname === 'billingftth.my.id') {
      // Produksi (Sudah Benar)
      wsUrl = `${protocol}//${hostname}/ws/notifications?token=${token}`;
  } else {
      // Lokal - Gunakan konfigurasi dari environment variable jika tersedia
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
      // Ubah http:// ke ws:// atau https:// ke wss://
      const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss:' : 'ws:';
      const wsHost = API_BASE_URL.replace(/^https?:\/\//, '');
      wsUrl = `${wsProtocol}//${wsHost}/ws/notifications?token=${token}`; 
  }

  // 3. Buat koneksi dengan URL yang sudah pasti benar
  console.log(`[WebSocket] Mencoba terhubung ke ${wsUrl}`);
  socket = new WebSocket(wsUrl);

  // --- Sisa event handler (onopen, onmessage, dll.) bisa tetap sama ---
  socket.onopen = () => {
    console.log('[WebSocket] Koneksi berhasil dibuat.');

    // Hentikan interval yang mungkin sudah ada
    if (pingInterval) clearInterval(pingInterval);
    if (tokenCheckInterval) clearInterval(tokenCheckInterval);

    // Setup ping interval
    pingInterval = setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send('ping');
      }
    }, 30000);

    // Setup token health check interval
    tokenCheckInterval = setInterval(async () => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        // Verify token validity setiap menit
        const isValid = await authStore.verifyToken();
        if (!isValid) {
          console.log('[WebSocket] Token no longer valid, refreshing...');
          if (tokenCheckInterval) {
            clearInterval(tokenCheckInterval);
            tokenCheckInterval = null;
          }
          await refreshTokenAndReconnect();
        }
      }
    }, 60000); // Check every minute
  };

  socket.onmessage = (event) => {
    // Filter out system messages sebelum processing
    if (event.data === 'pong' || event.data === 'ping') {
      return; // Silent filter for system messages
    }

    try {
      // PERBAIKAN: Validasi data sebelum parsing
      if (!event.data) {
        console.warn('[WebSocket] Received empty message');
        return;
      }

      let data;
      if (typeof event.data === 'string') {
        try {
          data = JSON.parse(event.data);
        } catch (parseError) {
          console.error('[WebSocket] Gagal parse JSON:', parseError);
          console.error('[WebSocket] Raw data:', event.data);
          return;
        }
      } else {
        data = event.data;
      }
      
      // PERBAIKAN: Validasi struktur data
      if (!data || typeof data !== 'object') {
        console.warn('[WebSocket] Invalid data format received:', data);
        return;
      }

      // Filter out ping/pong messages in JSON format
      if (data.type === 'ping' || data.type === 'pong') {
        return; // Silent filter for system messages
      }
      
      // PERBAIKAN: Pastikan notifications.value adalah array
      if (!notifications.value || !Array.isArray(notifications.value)) {
        console.warn('[WebSocket] notifications.value bukan array, inisialisasi ulang...');
        notifications.value = [];
      }
      
      // PERBAIKAN: Filter notifikasi yang tidak relevan
      // Jangan tampilkan notifikasi dengan action seperti auth/logout
      if (data.action && data.action.includes('/auth/')) {
        console.log('[WebSocket] Skipping auth-related notification:', data.action);
        return;
      }
      
      // PERBAIKAN: Tambahkan ID unik jika tidak ada
      if (!data.id) {
        data.id = Date.now() + Math.floor(Math.random() * 10000);
        console.log('[WebSocket] Generated ID for notification:', data.id);
      }
      
      // PERBAIKAN: Validasi dan normalisasi type notifikasi
      const validTypes = ['new_payment', 'new_technical_data', 'new_customer_for_noc', 'new_customer'];
      
      // Normalisasi tipe notifikasi
      if (data.type === 'new_customer') {
        // Konversi new_customer ke new_customer_for_noc untuk konsistensi
        data.type = 'new_customer_for_noc';
        console.log('[WebSocket] Normalized notification type from new_customer to new_customer_for_noc');
      }
      
      // Hanya proses notifikasi dengan tipe yang valid
      if (validTypes.includes(data.type)) {
        // PERBAIKAN: Tambahkan timestamp jika tidak ada
        if (!data.timestamp) {
          data.timestamp = new Date().toISOString();
        }
        
        // PERBAIKAN: Tambahkan message default jika tidak ada
        if (!data.message) {
          switch (data.type) {
            case 'new_payment':
              data.message = `Pembayaran baru diterima${data.data?.pelanggan_nama ? ` dari ${data.data.pelanggan_nama}` : ''}`;
              break;
            case 'new_customer_for_noc':
              data.message = `Pelanggan baru${data.data?.pelanggan_nama ? ` '${data.data.pelanggan_nama}'` : ''} telah ditambahkan`;
              break;
            case 'new_technical_data':
              data.message = `Data teknis baru${data.data?.pelanggan_nama ? ` untuk ${data.data.pelanggan_nama}` : ''} telah ditambahkan`;
              break;
            default:
              data.message = 'Notifikasi baru diterima';
          }
        }
        
        // PERBAIKAN: Pastikan data object ada
        if (!data.data) {
          data.data = {};
        }
        
        // PERBAIKAN: Filter notifikasi dengan data kosong
        // Jangan tampilkan notifikasi jika data penting tidak ada
        if (data.type === 'new_payment' && !data.data.invoice_number) {
          console.log('[WebSocket] Skipping new_payment notification without invoice_number');
          return;
        }
        if ((data.type === 'new_customer_for_noc' || data.type === 'new_customer') && !data.data.pelanggan_nama) {
          console.log('[WebSocket] Skipping new_customer notification without pelanggan_nama');
          return;
        }
        if (data.type === 'new_technical_data' && !data.data.pelanggan_nama) {
          console.log('[WebSocket] Skipping new_technical_data notification without pelanggan_nama');
          return;
        }
        
        // PERBAIKAN: Gunakan unshift alih-alih spread operator untuk performa dan konsistensi
        notifications.value.unshift(data);
        
        // Batasi jumlah notifikasi maksimal 20
        if (notifications.value.length > 20) {
          notifications.value = notifications.value.slice(0, 20);
        }
        
        console.log('[WebSocket] Notification added to list:', data.type, data.message);
        
        // PERBAIKAN: Play sound dengan validasi
        playSound(data.type);
        
        // PERBAIKAN: Dispatch event dengan validasi
        if (typeof window !== 'undefined' && window.dispatchEvent) {
          window.dispatchEvent(new CustomEvent('new-notification', { detail: data }));
        }
        
        console.log('[WebSocket] Notification processed successfully:', data.type);
      } else {
        // Jangan tampilkan notifikasi dengan tipe unknown
        console.warn('[WebSocket] Unknown notification type (filtered out):', data.type, data);
      }
      
    } catch (error) {
      console.error('[WebSocket] Gagal mem-parse pesan:', error);
      console.error('[WebSocket] Raw message:', event.data);
    }
  };

  socket.onerror = (error) => {
    console.error('[WebSocket] Terjadi error:', error);
    socket?.close();
  };

  socket.onclose = (event) => {
    console.warn(`[WebSocket] Koneksi ditutup: Kode ${event.code}`);
    socket = null;

    // Clean up all intervals
    if (pingInterval) clearInterval(pingInterval);
    if (tokenCheckInterval) clearInterval(tokenCheckInterval);

    // Don't reconnect if it's a normal closure or connection replacement
    const shouldNotReconnect = [1000, 1001, 1005].includes(event.code) ||
                               event.reason === "Connection replaced" ||
                               event.reason === "Logout Pengguna";

    if (authStore.isAuthenticated && !shouldNotReconnect) {
      // Check if closed due to token expiration (code 1008 = Policy Violation)
      if (event.code === 1008) {
        console.log('[WebSocket] Connection closed due to token policy, attempting refresh...');
        reconnectTimeout = setTimeout(refreshTokenAndReconnect, 1000);
      } else {
        console.log('[WebSocket] Menjadwalkan reconnect dalam 5 detik...');
        reconnectTimeout = setTimeout(connectWebSocket, 5000);
      }
    } else if (shouldNotReconnect) {
      console.log(`[WebSocket] Tidak reconnect karena penutupan normal: ${event.reason || event.code}`);
    }
  };
}

function disconnectWebSocket() {
  console.log('[WebSocket] Memutuskan koneksi secara manual...');
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }
  if (pingInterval) {
    clearInterval(pingInterval);
    pingInterval = null;
  }
  if (notificationCleanupInterval) {
    clearInterval(notificationCleanupInterval);
    notificationCleanupInterval = null;
  }
  if (tokenCheckInterval) {
    clearInterval(tokenCheckInterval);
    tokenCheckInterval = null;
  }

  if (socket) {
    socket.onclose = null; // Hapus listener onclose agar tidak memicu reconnect
    socket.close(1000, "Logout Pengguna");
    socket = null;
  }
}
// --- AKHIR BLOK KODE WEBSOCKET ---


const menuGroups = ref([
    { title: 'DASHBOARD', items: [
      { 
        title: 'Dashboard', 
        icon: 'mdi-home-variant', 
        value: 'dashboard-group', 
        permission: 'view_dashboard',
        children: [
          { title: 'Dashboard Admin', icon: 'mdi-home-variant', to: '/dashboard', permission: 'view_dashboard' },
          { title: 'Dashboard Jakinet', icon: 'mdi-account-group', to: '/dashboard-pelanggan', permission: 'view_dashboard_pelanggan' }
        ]
      },
    ] },
  
  { title: 'FTTH', items: [
      { title: 'Data Pelanggan', icon: 'mdi-account-group-outline', value: 'pelanggan', to: '/pelanggan', permission: 'view_pelanggan' },
      { title: 'Langganan', icon: 'mdi-wifi-star', value: 'langganan', to: '/langganan', badge: suspendedCount, badgeColor: 'orange', permission: 'view_langganan' },
      { title: 'Data Teknis', icon: 'mdi-database-cog-outline', value: 'teknis', to: '/data-teknis', permission: 'view_data_teknis' },
      { title: 'Brand & Paket', icon: 'mdi-tag-multiple-outline', value: 'harga', to: '/harga-layanan', permission: 'view_brand_&_paket' },
  ]},
  { title: 'LAINNYA', items: [
    { title: 'Simulasi Harga', icon: 'mdi-calculator', value: 'kalkulator', to: '/kalkulator', permission: 'view_simulasi_harga' },
    { title: 'S&K', icon: 'mdi-file-document-outline', value: 'sk', to: '/syarat-ketentuan', permission: null } // <-- Tambahkan ini
  ]},
  { title: 'BILLING', items: [
    { title: 'Invoices', icon: 'mdi-file-document-outline', value: 'invoices', to: '/invoices', badge: 0, badgeColor: 'grey-darken-1', permission: 'view_invoices' },
    { title: 'Laporan Pendapatan', icon: 'mdi-chart-line', value: 'revenue-report', to: '/reports/revenue', permission: 'view_reports_revenue' }
  ]},
  { title: 'NETWORK MANAGEMENT', items: [
    { title: 'Mikrotik Servers', icon: 'mdi-server', value: 'mikrotik', to: '/mikrotik', permission: 'view_mikrotik_servers' },
    { title: 'OLT Management', icon: 'mdi-router-network', value: 'olt', to: '/network-management/olt', permission: 'view_olt' },
    { title: 'ODP Management', icon: 'mdi-sitemap', value: 'odp', to: '/odp-management', permission: 'view_odp_management' },
    { title: 'Manajemen Inventaris', icon: 'mdi-archive-outline', value: 'inventory', to: '/inventory', permission: 'view_inventory' }
  ]},
  { title: 'MANAGEMENT', items: [
      { title: 'Users', icon: 'mdi-account-cog-outline', value: 'users', to: '/users', badge: userCount, badgeColor: 'primary', permission: 'view_users' },
      { title: 'Roles', icon: 'mdi-shield-account-outline', value: 'roles', to: '/roles', badge: roleCount, badgeColor: 'primary', permission: 'view_roles' },
      { title: 'Permissions', icon: 'mdi-shield-key-outline', value: 'permissions', to: '/permissions', permission: 'view_permissions' },
      { title: 'Activity Log', icon: 'mdi-history', value: 'activity-logs', to: '/activity-logs', permission: 'view_activity_log' },
      { title: 'Kelola S&K', icon: 'mdi-file-edit-outline', value: 'sk-management', to: '/management/sk', permission: 'manage_sk' },
      { title: 'Pengaturan', icon: 'mdi-cog-outline', value: 'settings', to: '/management/settings', permission: 'manage_settings' }
  ]},
]);

const filteredMenuGroups = computed(() => {
  if (userPermissions.value.includes('*')) return menuGroups.value;
  return menuGroups.value.map(group => ({
    ...group,
    items: group.items.filter(item => !item.permission || userPermissions.value.includes(item.permission)),
  })).filter(group => group.items.length > 0);
});



onMounted(async () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) theme.change(savedTheme);


  await settingsStore.fetchMaintenanceStatus(); 

  // Set drawer behavior based on screen size
  if (isMobile.value) {
    drawer.value = false;
    rail.value = false;
  }

  const enableAudioContext = () => {
    // Fungsi ini akan dijalankan sekali saat user mengklik
    // dan setelah itu listener-nya akan dihapus.
    console.log('User interaction detected. Audio playback is now enabled for this session.');
    document.removeEventListener('click', enableAudioContext);
  };
  document.addEventListener('click', enableAudioContext);
  
  const userIsValid = await authStore.verifyToken();
  if (userIsValid && authStore.user?.role) {
    const role = authStore.user.role;
    if (typeof role === 'object' && role !== null && role.name) {
      if (role.name.toLowerCase() === 'admin') userPermissions.value = ['*'];
      else userPermissions.value = role.permissions?.map((p: any) => p.name) || [];
    }
    fetchRoleCount();
    fetchUserCount();
    // fetchSuspendedCount();
    fetchSidebarBadges();
    fetchUnreadNotifications(); // <-- PANGGIL FUNGSI UNTUK MENGAMBIL NOTIFIKASI
    connectWebSocket(); // Memulai WebSocket setelah user terverifikasi
    
    // Bersihkan notifikasi yang tidak relevan setiap 30 detik
    notificationCleanupInterval = setInterval(() => {
      if (notifications.value && Array.isArray(notifications.value)) {
        const validTypes = ['new_payment', 'new_technical_data', 'new_customer_for_noc', 'new_customer'];
        notifications.value = notifications.value.filter(notif => {
          // Filter out auth-related notifications
          if (notif.action && notif.action.includes('/auth/')) {
            return false;
          }
          
          // Filter out unknown types
          if (!validTypes.includes(notif.type)) {
            return false;
          }
          
          // Filter out notifications with missing data
          if (notif.type === 'new_payment' && !notif.data?.invoice_number) {
            return false;
          }
          if ((notif.type === 'new_customer_for_noc' || notif.type === 'new_customer') && !notif.data?.pelanggan_nama) {
            return false;
          }
          if (notif.type === 'new_technical_data' && !notif.data?.pelanggan_nama) {
            return false;
          }
          
          return true;
        });
      }
    }, 30000); // 30 detik
  }
});

onUnmounted(() => {
  disconnectWebSocket();
});

function toggleTheme() {
  const newTheme = theme.global.current.value.dark ? 'light' : 'dark';
  theme.change(newTheme);
  localStorage.setItem('theme', newTheme);
}

// --- FUNGSI BARU UNTUK MENGAMBIL NOTIFIKASI DARI DATABASE ---
async function fetchUnreadNotifications() {
  try {
    // Ganti dengan endpoint API Anda yang sebenarnya
    const response = await apiClient.get('/notifications/unread'); 
    // Filter notifikasi yang relevan saja
    const validTypes = ['new_payment', 'new_technical_data', 'new_customer_for_noc', 'new_customer'];
    const filteredNotifications = response.data.notifications.filter((notif: any) => {
      // Filter out auth-related notifications
      if (notif.action && notif.action.includes('/auth/')) {
        return false;
      }
      
      // Filter out unknown types
      if (!validTypes.includes(notif.type)) {
        return false;
      }
      
      // Filter out notifications with missing data
      if (notif.type === 'new_payment' && !notif.data?.invoice_number) {
        return false;
      }
      if ((notif.type === 'new_customer_for_noc' || notif.type === 'new_customer') && !notif.data?.pelanggan_nama) {
        return false;
      }
      if (notif.type === 'new_technical_data' && !notif.data?.pelanggan_nama) {
        return false;
      }
      
      return true;
    });
    
    notifications.value = filteredNotifications.slice(0, 20); // Batasi maksimal 20 notifikasi
  } catch (error) {
    console.error("Gagal mengambil notifikasi yang belum dibaca:", error);
  }
}

function getNotificationIcon(type: string) {
  switch (type) {
    case 'new_payment': return 'mdi-cash-check';
    case 'new_customer_for_noc': return 'mdi-account-plus-outline';
    case 'new_technical_data': return 'mdi-lan-connect';
    default: return 'mdi-bell-outline';
  }
}

function getNotificationColor(type: string) {
  switch (type) {
    case 'new_payment': return 'success';
    case 'new_customer_for_noc': return 'info';
    case 'new_technical_data': return 'cyan';
    default: return 'grey';
  }
}

async function handleNotificationClick(notification: any) {
  // PERBAIKAN: Validasi parameter dengan lebih baik
  console.log('[Notification] handleNotificationClick called with:', notification);
  
  if (!notification) {
    console.error("[Notification] Invalid notification object: null or undefined");
    alert("Notifikasi tidak valid. Silakan refresh halaman.");
    return;
  }
  
  // PERBAIKAN: Validasi struktur object notification
  if (typeof notification !== 'object') {
    console.error("[Notification] Invalid notification object type:", typeof notification, notification);
    alert("Notifikasi tidak valid. Silakan refresh halaman.");
    return;
  }
  
  // PERBAIKAN: Validasi ID notifikasi dengan lebih baik
  if (!notification.hasOwnProperty('id')) {
    console.error("[Notification] Notification object missing 'id' property:", notification);
    alert("Notifikasi tidak valid (missing ID). Silakan refresh halaman.");
    return;
  }
  
  const notificationId = notification.id;
  if (notificationId === undefined || notificationId === null || notificationId === '') {
    console.error("[Notification] Invalid notification ID:", notificationId);
    alert("Notifikasi tidak valid (invalid ID). Silakan refresh halaman.");
    return;
  }
  
  // PERBAIKAN: Validasi type notifikasi
  if (!notification.hasOwnProperty('type')) {
    console.warn("[Notification] Notification object missing 'type' property:", notification);
    // Jangan hentikan proses, lanjutkan dengan type default
    notification.type = 'unknown';
  }

  // Jangan proses notifikasi dengan tipe unknown
  if (notification.type === 'unknown') {
    console.warn("[Notification] Skipping unknown notification type:", notification);
    // Hapus notifikasi dari daftar
    if (notifications.value && Array.isArray(notifications.value)) {
      notifications.value = notifications.value.filter(n => n.id !== notificationId);
    }
    return;
  }

  console.log('[Notification] Processing notification click for ID:', notificationId);

  // 1. Tandai notifikasi sebagai sudah dibaca di backend
  try {
    // PERBAIKAN: Validasi API client sebelum panggil
    if (!apiClient) {
      throw new Error("API client not initialized");
    }
    
    console.log(`[Notification] Calling API to mark notification ${notificationId} as read`);
    
    // Ganti dengan endpoint API Anda
    const response = await apiClient.post(`/notifications/${notificationId}/mark-as-read`);
    console.log(`[Notification] API response for marking ${notificationId} as read:`, response.status);
    
    // 2. Hapus notifikasi dari daftar di frontend secara visual
    if (notifications.value && Array.isArray(notifications.value)) {
      console.log(`[Notification] Removing notification ${notificationId} from frontend list`);
      notifications.value = notifications.value.filter(n => {
        const match = n.id !== notificationId;
        console.log(`[Notification] Filter check - comparing ${n.id} !== ${notificationId} = ${match}`);
        return match;
      });
      console.log(`[Notification] Updated notifications list length: ${notifications.value.length}`);
    } else {
      console.warn("[Notification] notifications.value bukan array:", notifications.value);
      // Fallback: Inisialisasi ulang jika bukan array
      notifications.value = [];
    }

    // 3. Arahkan pengguna ke halaman yang relevan
    console.log(`[Notification] Redirecting based on type: ${notification.type}`);
    
    // Jangan redirect untuk notifikasi unknown
    if (notification.type === 'unknown') {
      console.log("[Notification] No redirect for unknown notification type");
      return;
    }
    
    if (notification.type === 'new_technical_data') {
      console.log("[Notification] Redirecting to /langganan");
      router.push('/langganan');
    } else if (notification.type === 'new_customer_for_noc' || notification.type === 'new_customer') {
      console.log("[Notification] Redirecting to /data-teknis");
      router.push('/data-teknis');
    } else if (notification.type === 'new_payment') {
      console.log("[Notification] Redirecting to /invoices");
      router.push('/invoices');
    } else {
      console.warn("[Notification] Unknown notification type, redirecting to home:", notification.type);
      // Fallback: Arahkan ke halaman default
      router.push('/');
    }

  } catch (error) {
    console.error("[Notification] Gagal menandai notifikasi sebagai sudah dibaca:", error);
    
    // PERBAIKAN: Tampilkan pesan error yang lebih informatif
    if (error instanceof Error) {
      // Cek apakah ini error 404
      const errorMessage = error.message.toLowerCase();
      if (errorMessage.includes('404') || errorMessage.includes('not found')) {
        console.warn("[Notification] Notifikasi tidak ditemukan di server, hapus dari daftar lokal");
        // Hapus notifikasi dari daftar lokal meskipun error
        if (notifications.value && Array.isArray(notifications.value)) {
          notifications.value = notifications.value.filter(n => n.id !== notificationId);
        }
        // Masih arahkan pengguna ke halaman yang relevan
        if (notification.type === 'new_technical_data') {
          router.push('/langganan');
        } else if (notification.type === 'new_customer_for_noc' || notification.type === 'new_customer') {
          router.push('/data-teknis');
        } else if (notification.type === 'new_payment') {
          router.push('/invoices');
        } else {
          router.push('/');
        }
      } else {
        // Tampilkan pesan error ke pengguna
        alert(`Gagal menandai notifikasi sebagai sudah dibaca: ${error.message}`);
      }
    } else {
      alert("Gagal menandai notifikasi sebagai sudah dibaca. Silakan coba lagi.");
    }
  }
}

async function markAllAsRead() {
  try {
    // PERBAIKAN: Validasi API client sebelum panggil
    if (!apiClient) {
      throw new Error("API client not initialized");
    }
    
    // Ganti dengan endpoint API Anda
    const response = await apiClient.post('/notifications/mark-all-as-read'); 
    
    // PERBAIKAN: Validasi response sebelum update UI
    if (response && response.status === 200) {
      // Kosongkan daftar di frontend hanya jika sukses
      if (notifications.value && Array.isArray(notifications.value)) {
        notifications.value = []; // Kosongkan daftar notifikasi
      } else {
        console.warn("[Notification] notifications.value bukan array, inisialisasi ulang...");
        notifications.value = [];
      }
      
      console.log("[Notification] Semua notifikasi telah ditandai sebagai sudah dibaca");
    } else {
      throw new Error(`Unexpected response status: ${response.status}`);
    }
    
  } catch (error) {
    console.error("[Notification] Gagal membersihkan notifikasi:", error);
    
    // PERBAIKAN: Tampilkan pesan error yang lebih informatif
    if (error instanceof Error) {
      alert(`Gagal membersihkan notifikasi: ${error.message}`);
    } else {
      alert("Gagal membersihkan notifikasi. Silakan coba lagi.");
    }
    
    // PERBAIKAN: Fallback ke penghapusan lokal jika API gagal
    console.warn("[Notification] Fallback ke penghapusan lokal...");
    if (notifications.value && Array.isArray(notifications.value)) {
      notifications.value = [];
    } else {
      notifications.value = [];
    }
  }
}



// async function fetchSuspendedCount() {
//   try {
//     const response = await apiClient.get('/langganan?status=Ditangguhkan');
//     suspendedCount.value = response.data.length;
//   } catch (error) {
//     console.error("Gagal mengambil jumlah langganan yang ditangguhkan:", error);
//   }
// }

async function fetchRoleCount() {
  try {
    const response = await apiClient.get('/roles/');
    roleCount.value = response.data.length;
  } catch (error) {
    console.error("Gagal mengambil jumlah roles:", error);
  }
}

async function fetchUserCount() {
  try {
    const response = await apiClient.get('/users/');
    userCount.value = response.data.length;
  } catch (error) {
    console.error("Gagal mengambil jumlah users:", error);
  }
}

function handleLogout() {
  disconnectWebSocket();
  authStore.logout();
  router.push('/login');
}
</script>

<style scoped>
/* LIGHT THEME */
.modern-app {
  background-color: rgb(var(--v-theme-background));
  transition: background-color 0.3s ease;
}

.notification-content {
  cursor: pointer;
}

.nav-sub-item {
  border-radius: 10px;
  margin-bottom: 4px;
  color: rgba(var(--v-theme-on-surface), 0.8);
  min-height: 44px;
  transition: all 0.3s ease;
  /* Mengurangi padding kiri untuk menyelaraskan dengan parent */
  padding-left: 16px !important;
  /* Atau gunakan margin-left negatif untuk menarik ke kiri */
  margin-left: -8px;
}

.nav-sub-item .v-list-item-title {
  font-size: 0.9rem;
  font-weight: 500;
}

.nav-sub-item:not(.v-list-item--active):hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  transform: translateX(2px);
}

/* Alternatif lain - override Vuetify's default indentation */
.v-list-group .v-list-item {
  padding-inline-start: 16px !important;
}

/* Atau gunakan custom class untuk lebih spesifik */
.nav-sub-item.v-list-item {
  padding-inline-start: 16px !important;
  margin-inline-start: 0 !important;
}

.modern-drawer {
  border-right: none;
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.08);
  overflow: hidden !important;
  transition: all 0.3s ease;
}

.modern-drawer :deep(.v-navigation-drawer__content) {
  overflow: hidden !important;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.notification-item .v-list-item-subtitle {
  white-space: normal !important;      /* Izinkan teks untuk wrap ke baris baru */
  line-height: 1.4;                  /* Perbaiki jarak antar baris agar mudah dibaca */
  -webkit-line-clamp: 2; 
  line-clamp: 2;              /* Batasi teks hingga 2 baris */
  -webkit-box-orient: vertical;
  display: -webkit-box;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notification-item.v-list-item {
  min-height: 60px !important;         /* Beri tinggi minimal untuk menampung 2 baris */
  height: auto !important;             /* Biarkan tinggi item menyesuaikan konten */
  align-items: center;               /* Posisikan avatar dan teks di tengah */
}

.sidebar-header {
  height: 65px;
  padding: 0 11.5px !important;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
  transition: border-color 0.3s ease;
}

.header-flex-container {
  display: flex;
  align-items: center;
  width: 100%;
}

.sidebar-logo-full {
  height: 45px;
  margin-right: 12px;
  flex-shrink: 0;
  filter: brightness(1);
  transition: filter 0.3s ease;
}

/* Dark mode logo adjustment */
.v-theme--dark .sidebar-logo-full {
  filter: brightness(1.2) contrast(1.1);
}

.sidebar-title-wrapper {
  overflow: hidden;
  white-space: nowrap;
}

.sidebar-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
  margin-bottom: 2px;
  transition: color 0.3s ease;
}

.sidebar-subtitle {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: color 0.3s ease;
}

.navigation-wrapper {
  flex: 2;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 0;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.navigation-wrapper::-webkit-scrollbar {
  display: none;
}

.navigation-menu {
  padding: 0 16px;
}

.menu-subheader {
  font-size: 0.7rem;
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.6) !important;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-top: 20px;
  margin-bottom: 8px;
  padding: 0 16px;
  transition: color 0.3s ease;
}

.nav-item {
  border-radius: 10px;
  margin-bottom: 4px;
  color: rgba(var(--v-theme-on-surface), 0.8);
  min-height: 44px;
  transition: all 0.3s ease;
}

.nav-item .v-list-item-title {
  font-size: 0.9rem;
  font-weight: 500;
}

.nav-item:not(.v-list-item--active):hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  transform: translateX(2px);
}

.v-list-item--active {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  color: white !important;
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
}

.v-list-item--active .v-list-item-title {
  font-weight: 600;
}

.badge-chip {
  font-size: 0.7rem;
  height: 20px;
  font-weight: 600;
  border-radius: 10px;
  /* Hapus 'color: white;' dari sini agar warna default Vuetify berlaku */
}

/* Tambahkan aturan baru ini */
.v-list-item--active .badge-chip {
  color: white !important; /* Jadikan warna teks putih HANYA saat item aktif */
}

.logout-section {
  flex-shrink: 0;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgba(var(--v-theme-surface), 0.5);
  transition: all 0.3s ease;
}

.logout-btn {
  border-radius: 10px;
  font-weight: 500;
  text-transform: none;
  letter-spacing: normal;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background-color: #ef4444 !important;
  color: white !important;
}

.modern-app-bar {
  background: rgb(var(--v-theme-surface)) !important;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.header-action-btn {
  color: rgba(var(--v-theme-on-surface), 0.8);
  transition: all 0.3s ease;
}

.header-action-btn:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
}

.theme-toggle-btn:hover {
  background-color: rgba(var(--v-theme-warning), 0.1) !important;
  color: rgb(var(--v-theme-warning)) !important;
}

.modern-main {
  background-color: rgb(var(--v-theme-background));
  transition: background-color 0.3s ease;
}

.maintenance-banner {
  /* Memperbesar tinggi banner */
  height: 50px !important; 
  
  /* Memperbesar ukuran font */
  font-size: 2rem !important; 
  
  /* Membuat teks sedikit lebih tebal */
  font-weight: 600;

  /* Memastikan konten berada di tengah secara horizontal */
  justify-content: center; 
}

/* Footer responsive */
.footer-responsive {
  padding: 0 1rem;
}

.footer-content {
  text-align: center;
  font-size: 0.85rem;
  line-height: 1.4;
}

/* DARK THEME SPECIFIC STYLES */
.v-theme--dark .modern-app {
  background-color: #0f172a;
}

.v-theme--dark .modern-drawer {
  background: #1e293b;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
}

.v-theme--dark .sidebar-header {
  border-bottom: 1px solid #334155;
}

.v-theme--dark .modern-app-bar {
  background: #1e293b !important;
  border-bottom: 1px solid #334155;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.v-theme--dark .logout-section {
  background: #0f1629;
  border-top: 1px solid #334155;
}

.v-theme--dark .nav-item:not(.v-list-item--active):hover {
  background-color: rgba(129, 140, 248, 0.15);
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .modern-drawer {
    width: 280px !important;
  }
  
  .sidebar-title {
    font-size: 1.15rem;
  }
  
  .sidebar-subtitle {
    font-size: 0.7rem;
  }
  
  .nav-item {
    min-height: 48px;
  }
  
  .nav-item .v-list-item-title {
    font-size: 0.9rem;
  }
  
  .menu-subheader {
    font-size: 0.68rem;
  }
  
  .footer-content {
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .modern-drawer {
    width: 260px !important;
  }
  
  .sidebar-logo-full {
    height: 40px;
  }
  
  .sidebar-title {
    font-size: 1.1rem;
  }
  
  .sidebar-subtitle {
    font-size: 0.65rem;
  }
  
  .nav-item .v-list-item-title {
    font-size: 0.85rem;
  }
  
  .menu-subheader {
    font-size: 0.65rem;
  }
  
  .footer-content {
    font-size: 0.75rem;
    padding: 0.5rem 0;
  }
}

@media (max-width: 360px) {
  .modern-drawer {
    width: 240px !important;
  }
  
  .sidebar-logo-full {
    height: 35px;
  }
  
  .sidebar-title {
    font-size: 1rem;
  }
  
  .sidebar-subtitle {
    font-size: 0.6rem;
  }
  
  .nav-item .v-list-item-title {
    font-size: 0.8rem;
  }
  
  .footer-content {
    font-size: 0.7rem;
  }
}
</style>