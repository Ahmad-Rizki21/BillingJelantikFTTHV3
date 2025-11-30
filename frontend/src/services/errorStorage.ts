/**
 * Secure Error Storage Service
 * Menyimpan error details di session storage tanpa exposed di URL
 */

export interface SecureErrorDetails {
  id: string;
  timestamp: number;
  errorType: 'network' | 'server' | 'timeout' | 'unknown';
  errorStatus?: number;
  url?: string;
  method?: string;
  message?: string;
  userAgent: string;
}

class ErrorStorageService {
  private readonly STORAGE_KEY = 'network_error_details';
  private readonly MAX_AGE = 5 * 60 * 1000; // 5 minutes
  private readonly MAX_ERRORS = 10;

  /**
   * Simpan error details secara aman
   */
  storeError(errorType: string, errorStatus: number | string, url?: string, method?: string, message?: string): string {
    try {
      const errorId = `ERR-${Date.now().toString(36).toUpperCase()}`;

      // Sanitize sensitive information
      const sanitizedUrl = this.sanitizeUrl(url || '');
      const sanitizedMessage = this.sanitizeMessage(message || '');

      const errorDetails: SecureErrorDetails = {
        id: errorId,
        timestamp: Date.now(),
        errorType: errorType as any,
        errorStatus: typeof errorStatus === 'number' ? errorStatus : 0,
        url: sanitizedUrl,
        method: method?.toUpperCase(),
        message: sanitizedMessage,
        userAgent: navigator.userAgent
      };

      // Get existing errors
      const existingErrors = this.getStoredErrors();

      // Add new error
      existingErrors.push(errorDetails);

      // Clean old errors and limit size
      this.cleanExpiredErrors(existingErrors);
      this.limitErrors(existingErrors);

      // Save to session storage (not persistent)
      sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(existingErrors));

      return errorId;
    } catch (error) {
      console.warn('Failed to store error details:', error);
      return 'ERR-UNKNOWN';
    }
  }

  /**
   * Ambil error details berdasarkan ID
   */
  getError(errorId: string): SecureErrorDetails | null {
    try {
      const errors = this.getStoredErrors();
      const error = errors.find(e => e.id === errorId);

      if (error) {
        // Remove from storage after retrieval (one-time use)
        this.removeError(errorId);
        return error;
      }

      return null;
    } catch (error) {
      console.warn('Failed to retrieve error details:', error);
      return null;
    }
  }

  /**
   * Sanitize URL untuk menghilangkan sensitive paths
   */
  private sanitizeUrl(url: string): string {
    try {
      const urlObj = new URL(url, window.location.origin);

      // Blacklist sensitive paths
      const sensitivePaths = [
        '/auth/',
        '/api/',
        '/admin/',
        '/users/',
        '/login',
        '/token',
        '/password',
        '/reset'
      ];

      // Check if path contains sensitive information
      for (const sensitivePath of sensitivePaths) {
        if (urlObj.pathname.includes(sensitivePath)) {
          return '[REDACTED]';
        }
      }

      // Return generic path info
      return urlObj.pathname;
    } catch {
      return '[REDACTED]';
    }
  }

  /**
   * Sanitize error message untuk menghilangkan sensitive info
   */
  private sanitizeMessage(message: string): string {
    if (!message) return '';

    // Remove potential sensitive information
    let sanitized = message;

    // Remove URLs
    sanitized = sanitized.replace(/https?:\/\/[^\s]+/g, '[REDACTED_URL]');

    // Remove file paths
    sanitized = sanitized.replace(/\/[a-zA-Z0-9_\-\/\.]+/g, '[REDACTED_PATH]');

    // Remove potential credentials
    sanitized = sanitized.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[REDACTED_EMAIL]');
    sanitized = sanitized.replace(/password[=:]\S+/gi, 'password=[REDACTED]');
    sanitized = sanitized.replace(/token[=:]\S+/gi, 'token=[REDACTED]');

    // Limit length
    if (sanitized.length > 200) {
      sanitized = sanitized.substring(0, 197) + '...';
    }

    return sanitized.trim();
  }

  /**
   * Get all stored errors
   */
  private getStoredErrors(): SecureErrorDetails[] {
    try {
      const stored = sessionStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  /**
   * Remove expired errors
   */
  private cleanExpiredErrors(errors: SecureErrorDetails[]): void {
    const now = Date.now();
    for (let i = errors.length - 1; i >= 0; i--) {
      if (now - errors[i].timestamp > this.MAX_AGE) {
        errors.splice(i, 1);
      }
    }
  }

  /**
   * Limit number of stored errors
   */
  private limitErrors(errors: SecureErrorDetails[]): void {
    if (errors.length > this.MAX_ERRORS) {
      errors.splice(0, errors.length - this.MAX_ERRORS);
    }
  }

  /**
   * Remove specific error by ID
   */
  private removeError(errorId: string): void {
    try {
      const errors = this.getStoredErrors();
      const filtered = errors.filter(e => e.id !== errorId);
      sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(filtered));
    } catch {
      // Silently fail
    }
  }

  /**
   * Clear all errors
   */
  clearAll(): void {
    try {
      sessionStorage.removeItem(this.STORAGE_KEY);
    } catch {
      // Silently fail
    }
  }
}

// Export singleton instance
export const errorStorage = new ErrorStorageService();

// Rate limiting untuk network error redirects
export class NetworkErrorRateLimit {
  private readonly STORAGE_KEY = 'network_error_rate_limit';
  private readonly MAX_ATTEMPTS = 3;
  private readonly WINDOW_MS = 60 * 1000; // 1 minute

  canRedirect(): boolean {
    try {
      const data = this.getData();
      const now = Date.now();

      // Clean old attempts
      for (let i = data.attempts.length - 1; i >= 0; i--) {
        if (now - data.attempts[i] > this.WINDOW_MS) {
          data.attempts.splice(i, 1);
        }
      }

      // Check if under limit
      if (data.attempts.length >= this.MAX_ATTEMPTS) {
        return false;
      }

      // Add new attempt
      data.attempts.push(now);
      data.lastAttempt = now;

      sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
      return true;
    } catch {
      return true; // Allow if rate limiting fails
    }
  }

  private getData() {
    try {
      const stored = sessionStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : { attempts: [], lastAttempt: 0 };
    } catch {
      return { attempts: [], lastAttempt: 0 };
    }
  }
}

export const networkErrorRateLimit = new NetworkErrorRateLimit();