<template>
  <div style="height: 500px; width: 100%; border-radius: 8px; overflow: hidden">
    <div ref="mapContainer" style="width: 100%; height: 100%"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import mapboxgl, { Map, Marker, Popup } from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

// --- Tipe Data ---
interface ODP {
  id: number;
  kode_odp: string;
  alamat: string;
  latitude?: number;
  longitude?: number;
}

// --- Props ---
const props = defineProps({
  odps: {
    type: Array as () => ODP[],
    default: () => [],
  },
});

// --- Konfigurasi Mapbox ---
mapboxgl.accessToken = 'pk.eyJ1IjoiYWhtYWRkMjEyIiwiYSI6ImNtZmdsMjd0NTAxcjIybHNmZ250bW01OHkifQ.Ek4ISigA1wixiwK0KnFYmg';

const mapContainer = ref<HTMLDivElement | null>(null);
let map: Map | null = null;
let markers: Marker[] = [];

// --- Computed Property ---
const odpsWithCoords = computed(() => {
  return props.odps.filter(
    (odp) => odp.latitude != null && odp.longitude != null
  );
});

// --- Lifecycle Hooks ---
onMounted(() => {
  if (mapContainer.value && !map) {
    map = new Map({
      container: mapContainer.value,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [106.9756, -6.2383], // [longitude, latitude]
      zoom: 12,
    });

    // PERUBAHAN UTAMA: Tunggu sampai peta benar-benar selesai dimuat
    map.on('load', () => {
      // Setelah peta siap, baru kita 'awasi' perubahan data ODP
      watch(odpsWithCoords, (newOdps) => {
        if (!map) return; // Jaga-jaga jika map sudah di-destroy

        // Hapus marker lama dari peta
        markers.forEach(marker => marker.remove());
        markers = []; // Kosongkan array

        // Tambahkan marker baru untuk setiap ODP
        newOdps.forEach((odp) => {
          if (odp.longitude && odp.latitude) {
            const popupContent = `
              <div style="padding: 8px;">
                <div style="font-weight: bold;">${odp.kode_odp}</div>
                <div>${odp.alamat}</div>
              </div>
            `;

            const popup = new Popup({ offset: 25 }).setHTML(popupContent);

            const newMarker = new Marker()
              .setLngLat([odp.longitude, odp.latitude])
              .setPopup(popup)
              .addTo(map!);
            
            markers.push(newMarker);
          }
        });
      }, { immediate: true }); // immediate: true tetap penting untuk render pertama kali
    });
  }
});

onUnmounted(() => {
  map?.remove();
});

</script>