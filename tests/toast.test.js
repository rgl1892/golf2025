/**
 * Tests for ToastNotification Module
 */

import { ToastNotification } from '../superb_ock/static/superb_ock/js/modules/toast.js';

describe('ToastNotification', () => {
  let toast;

  beforeEach(() => {
    // Clear document body
    document.body.innerHTML = '';

    // Create new toast instance
    toast = new ToastNotification();
  });

  afterEach(() => {
    // Clean up
    if (toast) {
      toast.clear();
    }
    document.body.innerHTML = '';
  });

  describe('Initialization', () => {
    test('creates toast container on initialization', () => {
      const container = document.getElementById('toast-container');
      expect(container).toBeInTheDocument();
    });

    test('uses existing container if already present', () => {
      // Create another instance
      const toast2 = new ToastNotification();

      const containers = document.querySelectorAll('#toast-container');
      expect(containers.length).toBe(1);
    });

    test('injects styles only once', () => {
      // Create another instance
      const toast2 = new ToastNotification();

      const styles = document.querySelectorAll('#toast-styles');
      expect(styles.length).toBe(1);
    });

    test('applies correct position class', () => {
      const container = document.getElementById('toast-container');
      expect(container).toHaveClass('toast-top-right');
    });

    test('applies custom position', () => {
      document.body.innerHTML = '';
      const customToast = new ToastNotification({ position: 'bottom-left' });

      const container = document.getElementById('toast-container');
      expect(container).toHaveClass('toast-bottom-left');
    });
  });

  describe('show() method', () => {
    test('creates a toast element', () => {
      toast.show('Test message');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toBeInTheDocument();
    });

    test('displays correct message', () => {
      toast.show('Hello World');

      const message = document.querySelector('.toast-message');
      expect(message).toHaveTextContent('Hello World');
    });

    test('applies correct type class', () => {
      toast.show('Success!', 'success');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toHaveClass('toast-success');
    });

    test('includes correct icon for type', () => {
      toast.show('Success!', 'success');

      const icon = document.querySelector('.toast-icon');
      expect(icon.innerHTML).toContain('fa-check-circle');
    });

    test('includes close button', () => {
      toast.show('Test');

      const closeBtn = document.querySelector('.toast-close');
      expect(closeBtn).toBeInTheDocument();
      expect(closeBtn).toHaveAttribute('aria-label', 'Close');
    });

    test('adds toast to active toasts array', () => {
      toast.show('Test');
      expect(toast.activeToasts.length).toBe(1);
    });

    test('returns toast element', () => {
      const element = toast.show('Test');
      expect(element).toBeInstanceOf(HTMLElement);
    });
  });

  describe('Toast types', () => {
    test('success toast has correct styling', () => {
      toast.success('Success message');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toHaveClass('toast-success');
    });

    test('error toast has correct styling', () => {
      toast.error('Error message');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toHaveClass('toast-error');
    });

    test('warning toast has correct styling', () => {
      toast.warning('Warning message');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toHaveClass('toast-warning');
    });

    test('info toast has correct styling', () => {
      toast.info('Info message');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toHaveClass('toast-info');
    });
  });

  describe('Maximum toasts', () => {
    test('respects maximum toast limit', (done) => {
      // Show 4 toasts (max is 3)
      toast.show('Toast 1');
      toast.show('Toast 2');
      toast.show('Toast 3');
      toast.show('Toast 4');

      // Wait for removal animation
      setTimeout(() => {
        const toasts = document.querySelectorAll('.toast-notification');
        expect(toasts.length).toBe(3);
        done();
      }, 400);
    });

    test('removes oldest toast when limit reached', (done) => {
      toast.show('First toast');
      const firstToast = document.querySelector('.toast-notification');

      toast.show('Second toast');
      toast.show('Third toast');
      toast.show('Fourth toast');

      // Wait for removal animation
      setTimeout(() => {
        // First toast should be removed
        expect(firstToast).not.toBeInTheDocument();
        done();
      }, 400);
    });

    test('respects custom maxToasts setting', (done) => {
      document.body.innerHTML = '';
      const customToast = new ToastNotification({ maxToasts: 5 });

      // Show 6 toasts
      for (let i = 1; i <= 6; i++) {
        customToast.show(`Toast ${i}`);
      }

      setTimeout(() => {
        const toasts = document.querySelectorAll('.toast-notification');
        expect(toasts.length).toBe(5);
        done();
      }, 400);
    });
  });

  describe('remove() method', () => {
    test('removes toast from DOM', (done) => {
      const element = toast.show('Test');

      toast.remove(element);

      // Wait for animation
      setTimeout(() => {
        expect(element).not.toBeInTheDocument();
        done();
      }, 400);
    });

    test('removes toast from activeToasts array', (done) => {
      const element = toast.show('Test');
      expect(toast.activeToasts.length).toBe(1);

      toast.remove(element);

      setTimeout(() => {
        expect(toast.activeToasts.length).toBe(0);
        done();
      }, 400);
    });

    test('handles removing non-existent toast gracefully', () => {
      const fakeElement = document.createElement('div');

      expect(() => {
        toast.remove(fakeElement);
      }).not.toThrow();
    });

    test('adds hiding class before removal', () => {
      const element = toast.show('Test');

      toast.remove(element);

      expect(element).toHaveClass('hiding');
      expect(element).not.toHaveClass('show');
    });
  });

  describe('clear() method', () => {
    test('removes all toasts', (done) => {
      toast.show('Toast 1');
      toast.show('Toast 2');
      toast.show('Toast 3');

      toast.clear();

      setTimeout(() => {
        const toasts = document.querySelectorAll('.toast-notification');
        expect(toasts.length).toBe(0);
        done();
      }, 400);
    });

    test('clears activeToasts array', (done) => {
      toast.show('Toast 1');
      toast.show('Toast 2');

      toast.clear();

      setTimeout(() => {
        expect(toast.activeToasts.length).toBe(0);
        done();
      }, 400);
    });
  });

  describe('Close button', () => {
    test('clicking close button removes toast', (done) => {
      toast.show('Test');

      const closeBtn = document.querySelector('.toast-close');
      closeBtn.click();

      setTimeout(() => {
        const toasts = document.querySelectorAll('.toast-notification');
        expect(toasts.length).toBe(0);
        done();
      }, 400);
    });
  });

  describe('Auto-dismiss', () => {
    test('toast auto-dismisses after duration', (done) => {
      toast.show('Test', 'info', 100); // 100ms duration

      // Wait for duration + removal animation (100ms + 300ms)
      setTimeout(() => {
        const toasts = document.querySelectorAll('.toast-notification');
        expect(toasts.length).toBe(0);
        done();
      }, 500);
    });

    test('toast with duration=0 does not auto-dismiss', (done) => {
      toast.show('Test', 'info', 0);

      setTimeout(() => {
        const toasts = document.querySelectorAll('.toast-notification');
        expect(toasts.length).toBe(1);
        done();
      }, 200);
    });
  });

  describe('getIcon() method', () => {
    test('returns correct icon for success', () => {
      const icon = toast.getIcon('success');
      expect(icon).toContain('fa-check-circle');
    });

    test('returns correct icon for error', () => {
      const icon = toast.getIcon('error');
      expect(icon).toContain('fa-exclamation-circle');
    });

    test('returns correct icon for warning', () => {
      const icon = toast.getIcon('warning');
      expect(icon).toContain('fa-exclamation-triangle');
    });

    test('returns correct icon for info', () => {
      const icon = toast.getIcon('info');
      expect(icon).toContain('fa-info-circle');
    });

    test('returns empty string for unknown type', () => {
      const icon = toast.getIcon('unknown');
      expect(icon).toBe('');
    });
  });

  describe('Animation', () => {
    test('toast gets show class after creation', (done) => {
      toast.show('Test');

      const toastElement = document.querySelector('.toast-notification');

      setTimeout(() => {
        expect(toastElement).toHaveClass('show');
        done();
      }, 150);
    });
  });
});
