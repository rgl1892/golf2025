/**
 * Toast Notification Module
 * Simple toast notification system for user feedback
 */

class ToastNotification {
  constructor(options = {}) {
    this.defaultDuration = options.duration || 3000;
    this.position = options.position || 'top-right';
    this.maxToasts = options.maxToasts || 3;
    this.activeToasts = [];

    this.createContainer();
    this.injectStyles();
  }

  /**
   * Create the toast container if it doesn't exist
   */
  createContainer() {
    let container = document.getElementById('toast-container');

    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = `toast-container toast-${this.position}`;
      document.body.appendChild(container);
    }

    this.container = container;
  }

  /**
   * Inject toast styles into the page
   */
  injectStyles() {
    if (document.getElementById('toast-styles')) {
      return; // Styles already injected
    }

    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
      .toast-container {
        position: fixed;
        z-index: 9999;
        pointer-events: none;
      }

      .toast-container.toast-top-right {
        top: 20px;
        right: 20px;
      }

      .toast-container.toast-top-left {
        top: 20px;
        left: 20px;
      }

      .toast-container.toast-bottom-right {
        bottom: 20px;
        right: 20px;
      }

      .toast-container.toast-bottom-left {
        bottom: 20px;
        left: 20px;
      }

      .toast-notification {
        min-width: 250px;
        max-width: 350px;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        background: white;
        color: #333;
        font-size: 14px;
        line-height: 1.4;
        pointer-events: auto;
        transform: translateX(400px);
        opacity: 0;
        transition: transform 0.3s ease, opacity 0.3s ease;
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .toast-notification.show {
        transform: translateX(0);
        opacity: 1;
      }

      .toast-notification.hiding {
        transform: translateX(400px);
        opacity: 0;
      }

      /* Toast types */
      .toast-success {
        background: #d4edda;
        border-left: 4px solid #28a745;
        color: #155724;
      }

      .toast-error {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        color: #721c24;
      }

      .toast-warning {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        color: #856404;
      }

      .toast-info {
        background: #d1ecf1;
        border-left: 4px solid #17a2b8;
        color: #0c5460;
      }

      .toast-icon {
        font-size: 18px;
        flex-shrink: 0;
      }

      .toast-message {
        flex: 1;
      }

      .toast-close {
        background: none;
        border: none;
        font-size: 20px;
        line-height: 1;
        cursor: pointer;
        opacity: 0.5;
        padding: 0;
        flex-shrink: 0;
      }

      .toast-close:hover {
        opacity: 1;
      }

      /* Mobile responsive */
      @media (max-width: 768px) {
        .toast-container {
          left: 10px !important;
          right: 10px !important;
        }

        .toast-notification {
          max-width: 100%;
        }
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Show a toast notification
   * @param {string} message - The message to display
   * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
   * @param {number} duration - How long to show toast (ms)
   */
  show(message, type = 'info', duration = this.defaultDuration) {
    // Remove oldest toast if we're at max
    if (this.activeToasts.length >= this.maxToasts) {
      this.remove(this.activeToasts[0]);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;

    // Get icon based on type
    const icon = this.getIcon(type);

    // Build toast HTML
    toast.innerHTML = `
      ${icon ? `<span class="toast-icon">${icon}</span>` : ''}
      <span class="toast-message">${message}</span>
      <button class="toast-close" aria-label="Close">&times;</button>
    `;

    // Add to container
    this.container.appendChild(toast);
    this.activeToasts.push(toast);

    // Close button handler
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => this.remove(toast));

    // Show animation
    setTimeout(() => toast.classList.add('show'), 100);

    // Auto remove after duration
    if (duration > 0) {
      setTimeout(() => this.remove(toast), duration);
    }

    return toast;
  }

  /**
   * Get icon HTML for toast type
   * @param {string} type - Toast type
   * @returns {string} Icon HTML
   */
  getIcon(type) {
    const icons = {
      success: '<i class="fas fa-check-circle"></i>',
      error: '<i class="fas fa-exclamation-circle"></i>',
      warning: '<i class="fas fa-exclamation-triangle"></i>',
      info: '<i class="fas fa-info-circle"></i>'
    };
    return icons[type] || '';
  }

  /**
   * Remove a toast notification
   * @param {HTMLElement} toast - The toast element to remove
   */
  remove(toast) {
    if (!toast || !toast.parentNode) return;

    toast.classList.remove('show');
    toast.classList.add('hiding');

    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      this.activeToasts = this.activeToasts.filter(t => t !== toast);
    }, 300);
  }

  /**
   * Remove all active toasts
   */
  clear() {
    this.activeToasts.forEach(toast => this.remove(toast));
  }

  /**
   * Convenience methods for different toast types
   */
  success(message, duration) {
    return this.show(message, 'success', duration);
  }

  error(message, duration) {
    return this.show(message, 'error', duration);
  }

  warning(message, duration) {
    return this.show(message, 'warning', duration);
  }

  info(message, duration) {
    return this.show(message, 'info', duration);
  }
}

// ES6 export for module usage
export { ToastNotification };

// Create global instance for browser usage
if (typeof window !== 'undefined') {
  window.toast = new ToastNotification();
  window.ToastNotification = ToastNotification;
}
