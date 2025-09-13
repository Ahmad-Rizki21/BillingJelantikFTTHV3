// src/stores/auth.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import apiClient from '@/services/api';
import router from '@/router';

// Definisikan tipe data yang lebih spesifik
interface Permission {
  name: string;
}

interface Role {
  name: string;
  permissions: Permission[];
}

interface User {
  id: number;
  email: string;
  name: string;
  role: Role; // Pastikan role adalah objek
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'));
  const user = ref<User | null>(null);

  const isAuthenticated = computed(() => !!token.value);

  // Fungsi PENTING untuk memeriksa hak akses dari komponen
  function hasPermission(permissionName: string): boolean {
    if (!user.value?.role?.permissions) {
      return false;
    }
    return user.value.role.permissions.some(p => p.name === permissionName);
  }

  function setToken(newToken: string) {
    localStorage.setItem('access_token', newToken);
    token.value = newToken;
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
  }

  function logout() {
    localStorage.removeItem('access_token');
    token.value = null;
    user.value = null;
    delete apiClient.defaults.headers.common['Authorization'];
    router.push('/login');
  }

  async function verifyToken(): Promise<boolean> {
    if (!token.value) return false;
    try {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token.value}`;
      const response = await apiClient.get<User>('/users/me');
      user.value = response.data;
      return true;
    } catch (error) {
      console.error('Token verification failed:', error);
      logout();
      return false;
    }
  }

  async function login(email: string, password: string): Promise<boolean> {
    try {
      const response = await apiClient.post(
        '/users/token',
        `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
        {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        }
      );
      setToken(response.data.access_token);
      return await verifyToken();
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  }

  async function initializeAuth() {
    if (token.value) {
      await verifyToken();
    }
  }

  return {
    token,
    user,
    isAuthenticated,
    hasPermission, // Ekspor fungsi ini agar bisa dipakai
    setToken,
    logout,
    verifyToken,
    login,
    initializeAuth,
  };
});