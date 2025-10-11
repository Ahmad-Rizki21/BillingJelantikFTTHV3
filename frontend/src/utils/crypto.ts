/**
 * Utility functions for token encryption/decryption
 * This enhances security by storing tokens in encrypted format in localStorage
 */

// Simple XOR-based encryption for client-side (not for highly sensitive data)
// For production, consider using Web Crypto API for stronger encryption
const ENCRYPTION_KEY = 'ArtacomFTTH_2025_Secure_Key_Hashing';

/**
 * Encrypts a string using XOR cipher
 * @param text - Plain text to encrypt
 * @returns Encrypted string (base64 encoded)
 */
export function encrypt(text: string): string {
  if (!text) return '';

  try {
    let encrypted = '';
    for (let i = 0; i < text.length; i++) {
      encrypted += String.fromCharCode(
        text.charCodeAt(i) ^ ENCRYPTION_KEY.charCodeAt(i % ENCRYPTION_KEY.length)
      );
    }
    return btoa(encrypted); // base64 encode
  } catch (error) {
    console.error('Encryption failed:', error);
    return text; // fallback to plain text
  }
}

/**
 * Decrypts a string using XOR cipher
 * @param encryptedText - Encrypted string (base64 encoded)
 * @returns Decrypted plain text
 */
export function decrypt(encryptedText: string): string {
  if (!encryptedText) return '';

  try {
    const decoded = atob(encryptedText); // base64 decode
    let decrypted = '';
    for (let i = 0; i < decoded.length; i++) {
      decrypted += String.fromCharCode(
        decoded.charCodeAt(i) ^ ENCRYPTION_KEY.charCodeAt(i % ENCRYPTION_KEY.length)
      );
    }
    return decrypted;
  } catch (error) {
    console.error('Decryption failed:', error);
    return encryptedText; // fallback to original text (might be plain)
  }
}

/**
 * Encrypts and stores a token in localStorage
 * @param key - Storage key
 * @param token - Token to encrypt and store
 */
export function setEncryptedToken(key: string, token: string): void {
  if (!token) {
    localStorage.removeItem(key);
    return;
  }

  try {
    const encrypted = encrypt(token);
    localStorage.setItem(key, encrypted);
  } catch (error) {
    console.error('Failed to encrypt and store token:', error);
    // Fallback to plain storage if encryption fails
    localStorage.setItem(key, token);
  }
}

/**
 * Retrieves and decrypts a token from localStorage
 * @param key - Storage key
 * @returns Decrypted token or null
 */
export function getEncryptedToken(key: string): string | null {
  try {
    const encrypted = localStorage.getItem(key);
    if (!encrypted) return null;

    // Try to decrypt first
    const decrypted = decrypt(encrypted);

    // Validate if it's a valid JWT (starts with eyJ)
    if (decrypted.startsWith('eyJ')) {
      return decrypted;
    }

    // If not valid JWT, return as-is (might be old plain token)
    return encrypted;
  } catch (error) {
    console.error('Failed to retrieve and decrypt token:', error);
    return localStorage.getItem(key); // fallback
  }
}

/**
 * Removes encrypted token from localStorage
 * @param key - Storage key
 */
export function removeEncryptedToken(key: string): void {
  localStorage.removeItem(key);
}