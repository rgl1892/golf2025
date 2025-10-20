/**
 * Toast Notification Tests
 *
 * Tests for the ToastNotification module
 */

import { ToastNotification } from '../modules/toast.js';

describe('ToastNotification', () => {
  let toast;

  beforeEach(() => {
    // Clear DOM before each test
    document.body.innerHTML = '';
    // Create fresh instance
    toast = new ToastNotification();
    // Clear any timers
    jest.clearAllTimers();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Container creation', () => {
    test('creates container on initialization', () => {
      const container = document.getElementById('toast-container');
      expect(container).toBeInTheDocument();
      expect(container).toHaveClass('toast-container');
    });

    test('uses existing container if already present', () => {
      // The beforeEach already created a toast instance with a container
      // Creating a second instance should reuse the same container
      const secondToast = new ToastNotification();
      const containers = document.querySelectorAll('#toast-container');
      expect(containers).toHaveLength(1);
      expect(secondToast.container).toBe(toast.container);
    });
  });

  describe('Toast display', () => {
    test('creates success toast with correct styling', () => {
      toast.success('Test success message');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toBeInTheDocument();
      expect(toastElement).toHaveClass('toast-success');
      expect(toastElement).toHaveTextContent('Test success message');
    });

    test('creates error toast with correct styling', () => {
      toast.error('Test error message');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toHaveClass('toast-error');
      expect(toastElement).toHaveTextContent('Test error message');
    });

    test('creates warning toast with correct styling', () => {
      toast.warning('Test warning message');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toHaveClass('toast-warning');
      expect(toastElement).toHaveTextContent('Test warning message');
    });

    test('creates info toast with correct styling', () => {
      toast.info('Test info message');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toHaveClass('toast-info');
      expect(toastElement).toHaveTextContent('Test info message');
    });

    test('includes icon in toast', () => {
      toast.success('Test message');

      const iconContainer = document.querySelector('.toast-icon');
      expect(iconContainer).toBeInTheDocument();

      const icon = iconContainer.querySelector('.fas');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Toast positioning', () => {
    test('positions toast correctly', () => {
      // Clear the container created by beforeEach
      document.body.innerHTML = '';

      const customToast = new ToastNotification({ position: 'top-left' });
      const container = document.getElementById('toast-container');
      expect(container).toHaveClass('toast-top-left');
    });
  });

  describe('Toast auto-dismiss', () => {
    test('removes toast after duration', () => {
      toast.success('Test message');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toBeInTheDocument();

      // Fast-forward time
      jest.advanceTimersByTime(3500);

      expect(toastElement).not.toBeInTheDocument();
    });

    test('respects custom duration', () => {
      const customToast = new ToastNotification({ duration: 1000 });
      customToast.success('Test message');

      const toastElement = document.querySelector('.toast-notification');
      expect(toastElement).toBeInTheDocument();

      jest.advanceTimersByTime(1500);

      expect(toastElement).not.toBeInTheDocument();
    });
  });

  describe('Toast limit', () => {
    test('respects maximum toast limit', () => {
      const customToast = new ToastNotification({ maxToasts: 3 });

      customToast.success('Message 1');
      customToast.success('Message 2');
      customToast.success('Message 3');
      customToast.success('Message 4'); // Should remove first

      // Wait for removal animation
      jest.advanceTimersByTime(350);

      const toasts = document.querySelectorAll('.toast-notification');
      expect(toasts).toHaveLength(3);
      expect(toasts[0]).toHaveTextContent('Message 2');
    });
  });

  describe('Close button', () => {
    test('closes toast when close button clicked', () => {
      toast.success('Test message');

      const toastElement = document.querySelector('.toast-notification');
      const closeButton = toastElement.querySelector('.toast-close');

      closeButton.click();

      // Wait for animation
      jest.advanceTimersByTime(350);

      expect(toastElement).not.toBeInTheDocument();
    });
  });

  describe('Animation', () => {
    test('adds show class for animation', () => {
      toast.success('Test message');

      const toastElement = document.querySelector('.toast-notification');

      jest.advanceTimersByTime(100);

      expect(toastElement).toHaveClass('show');
    });

    test('removes show class before dismissing', () => {
      toast.success('Test message');

      const toastElement = document.querySelector('.toast-notification');

      jest.advanceTimersByTime(3100); // After duration but before removal

      expect(toastElement).not.toHaveClass('show');
    });
  });
});
