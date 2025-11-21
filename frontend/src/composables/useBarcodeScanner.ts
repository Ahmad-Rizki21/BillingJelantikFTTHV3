import { ref } from 'vue';

export type BarcodeType = 'en' | 'serial' | 'mac' | 'unknown';

export interface BarcodeScanResult {
  value: string;
  type: BarcodeType;
  formatted?: string;
  isValid: boolean;
  message?: string;
}

export interface BarcodeScannerOptions {
  onSerialDetected?: (serial: string) => void;
  onMacDetected?: (mac: string) => void;
  onEnDetected?: (en: string) => void;
  onMultipleDetected?: (results: BarcodeScanResult[]) => void;
  autoClose?: boolean;
}

export function useBarcodeScanner(options: BarcodeScannerOptions = {}) {
  const isSerialScannerOpen = ref(false);
  const isMacScannerOpen = ref(false);
  const lastScannedSerial = ref('');
  const lastScannedMac = ref('');

  // Open Serial Number Scanner
  function openSerialScanner() {
    isSerialScannerOpen.value = true;
  }

  // Open MAC Address Scanner
  function openMacScanner() {
    isMacScannerOpen.value = true;
  }

  // Close all scanners
  function closeAllScanners() {
    isSerialScannerOpen.value = false;
    isMacScannerOpen.value = false;
  }

  // Handle serial number detection
  function handleSerialDetected(serial: string) {
    lastScannedSerial.value = serial;
    options.onSerialDetected?.(serial);

    if (options.autoClose !== false) {
      isSerialScannerOpen.value = false;
    }
  }

  // Handle MAC address detection
  function handleMacDetected(mac: string) {
    lastScannedMac.value = mac;
    options.onMacDetected?.(mac);

    if (options.autoClose !== false) {
      isMacScannerOpen.value = false;
    }
  }

  // USB Scanner helpers - optimized for external barcode scanners
  function formatMacAddress(input: string): string {
    // Remove all non-hex characters
    const cleaned = input.replace(/[^a-fA-F0-9]/g, '');

    // If exactly 12 hex characters, format as MAC address
    if (cleaned.length === 12) {
      return cleaned.match(/.{1,2}/g)?.join(':').toUpperCase() || '';
    }

    return cleaned; // Return as is if not 12 chars (for manual input validation)
  }

  function formatSerialNumber(input: string): string {
    // Remove unwanted characters, keep alphanumeric, dashes, underscores
    return input.replace(/[^A-Za-z0-9\-_]/g, '').toUpperCase();
  }

  function isValidMacAddress(mac: string): boolean {
    const macRegex = /^([0-9A-F]{2}:){5}[0-9A-F]{2}$/i;
    return macRegex.test(mac);
  }

  function validateMacForUSBScanner(input: string): { valid: boolean; formatted?: string; message?: string } {
    const cleaned = input.replace(/[^a-fA-F0-9]/g, '').toUpperCase();

    if (cleaned.length === 0) {
      return { valid: false, message: 'MAC Address tidak boleh kosong' };
    }

    if (cleaned.length !== 12) {
      return { valid: false, message: `MAC Address harus 12 karakter hexadesimal, dapat ${cleaned.length} karakter` };
    }

    if (!/^[0-9A-F]+$/.test(cleaned)) {
      return { valid: false, message: 'MAC Address hanya boleh mengandung 0-9 dan A-F' };
    }

    const formatted = cleaned.match(/.{1,2}/g)?.join(':') || '';
    return { valid: true, formatted };
  }

  function validateSerialForUSBScanner(input: string): { valid: boolean; formatted?: string; message?: string } {
    const cleaned = input.replace(/[^A-Za-z0-9\-_]/g, '').toUpperCase();

    if (cleaned.length === 0) {
      return { valid: false, message: 'Serial Number tidak boleh kosong' };
    }

    if (cleaned.length > 100) {
      return { valid: false, message: 'Serial Number terlalu panjang (maksimal 100 karakter)' };
    }

    return { valid: true, formatted: cleaned };
  }

  // NEW: Detect barcode type based on format patterns
  function detectBarcodeType(input: string): BarcodeType {
    const cleaned = input.trim().toUpperCase();

    // MAC Address detection (12 hex chars, dengan/without separators)
    const macCleaned = cleaned.replace(/[^A-F0-9]/g, '');
    if (macCleaned.length === 12 && /^[A-F0-9]+$/.test(macCleaned)) {
      return 'mac';
    }

    // EN detection - Usually starts with specific prefixes or has certain patterns
    // Common EN patterns for telecom equipment:
    const enPatterns = [
      /^[A-Z]{2,4}\d{4,}/, // 2-4 letters followed by 4+ digits (e.g., "ZTEG12345")
      /^\d{2,3}[A-Z]{2,4}/, // 2-3 digits followed by 2-4 letters (e.g., "123XYZ")
      /^[A-Z]\d{6,}/, // 1 letter followed by 6+ digits (e.g., "S1234567")
      /^EN\d+/i, // Starts with "EN"
      /^EAN\d+/i, // Starts with "EAN"
      /^SKU\d+/i, // Starts with "SKU"
      /^P\/N\d+/i, // Starts with "P/N"
      /^PART\d+/i, // Starts with "PART"
      /^[A-Z]{3,5}\d{3,6}$/, // 3-5 letters + 3-6 digits (common part numbers)
    ];

    for (const pattern of enPatterns) {
      if (pattern.test(cleaned)) {
        return 'en';
      }
    }

    // Serial Number detection - Usually alphanumeric, longer, mixed patterns
    const serialPatterns = [
      /^[A-Z0-9]{8,}$/, // 8+ alphanumeric chars
      /^\d{6,}[A-Z]{2,}/, // 6+ digits followed by 2+ letters
      /^[A-Z]{2,}\d{6,}/, // 2+ letters followed by 6+ digits
      /^[A-Z0-9]{2}-[A-Z0-9]{3}-[A-Z0-9]{3,}$/, // Format XXX-XXX-XXX
      /^[A-Z0-9]{4}-[A-Z0-9]{4}$/, // Format XXXX-XXXX
    ];

    for (const pattern of serialPatterns) {
      if (pattern.test(cleaned)) {
        return 'serial';
      }
    }

    // Default to serial if it doesn't match EN or MAC patterns
    return 'unknown';
  }

  // NEW: Validate and process any barcode
  function processAnyBarcode(input: string): BarcodeScanResult {
    const type = detectBarcodeType(input);
    let formatted: string | undefined;
    let isValid = false;
    let message: string | undefined;

    switch (type) {
      case 'mac':
        const macResult = validateMacForUSBScanner(input);
        formatted = macResult.formatted;
        isValid = macResult.valid;
        message = macResult.message;
        break;

      case 'en':
        // EN validation - usually part numbers
        const enCleaned = input.replace(/[^A-Z0-9\-_\/]/g, '').toUpperCase();
        if (enCleaned.length === 0) {
          message = 'Equipment Number tidak valid';
        } else if (enCleaned.length > 50) {
          message = 'Equipment Number terlalu panjang';
        } else {
          formatted = enCleaned;
          isValid = true;
        }
        break;

      case 'serial':
        const serialResult = validateSerialForUSBScanner(input);
        formatted = serialResult.formatted;
        isValid = serialResult.valid;
        message = serialResult.message;
        break;

      default:
        // Try to validate as serial as fallback
        const fallbackResult = validateSerialForUSBScanner(input);
        formatted = fallbackResult.formatted;
        isValid = fallbackResult.valid;
        message = fallbackResult.message || 'Tidak dapat mengidentifikasi tipe barcode';
        break;
    }

    return {
      value: input.trim(),
      type,
      formatted: formatted || input.trim(),
      isValid,
      message
    };
  }

  // NEW: Handle multiple barcode scanning
  function processMultipleScan(results: BarcodeScanResult[]): { en?: string; serial?: string; mac?: string; hasConflict: boolean } {
    const processed: { en?: string; serial?: string; mac?: string; hasConflict: boolean } = {
      hasConflict: false
    };

    // Group results by type
    const grouped = results.reduce((acc, result) => {
      if (!acc[result.type]) {
        acc[result.type] = [];
      }
      if (result.isValid) {
        acc[result.type].push(result);
      }
      return acc;
    }, {} as Record<BarcodeType, BarcodeScanResult[]>);

    // Process each type (take the last valid one for each type)
    if (grouped.en && grouped.en.length > 0) {
      processed.en = grouped.en[grouped.en.length - 1].formatted;
    }

    if (grouped.serial && grouped.serial.length > 0) {
      processed.serial = grouped.serial[grouped.serial.length - 1].formatted;
    }

    if (grouped.mac && grouped.mac.length > 0) {
      processed.mac = grouped.mac[grouped.mac.length - 1].formatted;
    }

    // Check for conflicts (multiple valid entries of same type)
    Object.keys(grouped).forEach(type => {
      if (grouped[type as BarcodeType].length > 1) {
        processed.hasConflict = true;
      }
    });

    return processed;
  }

  return {
    // State
    isSerialScannerOpen,
    isMacScannerOpen,
    lastScannedSerial,
    lastScannedMac,

    // Methods
    openSerialScanner,
    openMacScanner,
    closeAllScanners,
    handleSerialDetected,
    handleMacDetected,

    // Utilities
    formatMacAddress,
    formatSerialNumber,
    isValidMacAddress,
    validateMacForUSBScanner,
    validateSerialForUSBScanner,

    // NEW: Multiple barcode detection
    detectBarcodeType,
    processAnyBarcode,
    processMultipleScan,
  };
}