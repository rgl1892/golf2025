/**
 * Accessibility Manager Module
 * Handles keyboard/mouse detection, table scroll indicators, and other a11y features
 */

class AccessibilityManager {
  constructor() {
    this.usingKeyboard = false;
    this.init();
  }

  /**
   * Initialize accessibility features
   */
  init() {
    this.detectInputMethod();
    this.setupTableScrollIndicators();
    this.setupFocusTrap();
    this.setupAriaLiveRegion();
  }

  /**
   * Detect whether user is using keyboard or mouse
   * Adds body classes for conditional focus styling
   */
  detectInputMethod() {
    // Detect keyboard usage
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        document.body.classList.add('using-keyboard');
        document.body.classList.remove('using-mouse');
        this.usingKeyboard = true;
      }
    });

    // Detect mouse usage
    document.addEventListener('mousedown', () => {
      document.body.classList.add('using-mouse');
      document.body.classList.remove('using-keyboard');
      this.usingKeyboard = false;
    });
  }

  /**
   * Set up scroll indicators for horizontally scrollable tables
   */
  setupTableScrollIndicators() {
    const containers = document.querySelectorAll('.table-responsive');

    containers.forEach(container => {
      // Wrap table in scroll container
      if (!container.classList.contains('table-scroll-container')) {
        container.classList.add('table-scroll-container');
      }

      // Check scroll position on scroll
      container.addEventListener('scroll', () => {
        this.updateScrollIndicators(container);
      });

      // Initial check
      this.updateScrollIndicators(container);

      // Recheck on window resize
      window.addEventListener('resize', () => {
        this.updateScrollIndicators(container);
      });
    });
  }

  /**
   * Update scroll indicators based on scroll position
   * @param {HTMLElement} container - The scrollable container
   */
  updateScrollIndicators(container) {
    const scrollLeft = container.scrollLeft;
    const scrollWidth = container.scrollWidth;
    const clientWidth = container.clientWidth;
    const maxScroll = scrollWidth - clientWidth;

    // Add class if scrolled from left edge
    if (scrollLeft > 10) {
      container.classList.add('scrolled-left');
    } else {
      container.classList.remove('scrolled-left');
    }

    // Add class if scrolled to right edge
    if (scrollLeft >= maxScroll - 10) {
      container.classList.add('scrolled-right');
    } else {
      container.classList.remove('scrolled-right');
    }
  }

  /**
   * Set up focus trap for modals
   * Keeps focus within modal when open
   */
  setupFocusTrap() {
    document.addEventListener('shown.bs.modal', (e) => {
      const modal = e.target;
      this.trapFocus(modal);
    });
  }

  /**
   * Trap focus within an element
   * @param {HTMLElement} element - Element to trap focus within
   */
  trapFocus(element) {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Focus first element
    firstElement.focus();

    // Handle tab key
    const handleTab = (e) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    element.addEventListener('keydown', handleTab);

    // Clean up on modal hide
    element.addEventListener('hidden.bs.modal', () => {
      element.removeEventListener('keydown', handleTab);
    }, { once: true });
  }

  /**
   * Set up ARIA live region for dynamic announcements
   */
  setupAriaLiveRegion() {
    // Create live region if it doesn't exist
    if (!document.getElementById('aria-live-region')) {
      const liveRegion = document.createElement('div');
      liveRegion.id = 'aria-live-region';
      liveRegion.className = 'aria-live-region';
      liveRegion.setAttribute('role', 'status');
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      document.body.appendChild(liveRegion);
    }
  }

  /**
   * Announce a message to screen readers
   * @param {string} message - Message to announce
   * @param {string} priority - 'polite' or 'assertive'
   */
  announce(message, priority = 'polite') {
    const liveRegion = document.getElementById('aria-live-region');
    if (!liveRegion) return;

    liveRegion.setAttribute('aria-live', priority);
    liveRegion.textContent = message;

    // Clear after announcement
    setTimeout(() => {
      liveRegion.textContent = '';
    }, 1000);
  }

  /**
   * Make an element keyboard accessible
   * @param {HTMLElement} element - Element to make accessible
   * @param {Function} callback - Function to call on Enter/Space
   */
  makeKeyboardAccessible(element, callback) {
    // Add tabindex if not already focusable
    if (!element.hasAttribute('tabindex')) {
      element.setAttribute('tabindex', '0');
    }

    // Add role if not already set
    if (!element.hasAttribute('role')) {
      element.setAttribute('role', 'button');
    }

    // Handle keyboard events
    element.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        callback(e);
      }
    });
  }

  /**
   * Add loading state with accessibility support
   * @param {HTMLElement} element - Element to show loading state
   * @param {string} message - Loading message for screen readers
   */
  showLoading(element, message = 'Loading...') {
    element.classList.add('loading');
    element.setAttribute('aria-busy', 'true');
    element.setAttribute('data-loading-message', message);
    this.announce(message);
  }

  /**
   * Remove loading state
   * @param {HTMLElement} element - Element to remove loading state from
   * @param {string} message - Completion message for screen readers
   */
  hideLoading(element, message = 'Loaded') {
    element.classList.remove('loading');
    element.setAttribute('aria-busy', 'false');
    element.removeAttribute('data-loading-message');
    this.announce(message);
  }

  /**
   * Check if user is using keyboard for navigation
   * @returns {boolean}
   */
  isUsingKeyboard() {
    return this.usingKeyboard;
  }

  /**
   * Add skip navigation link
   */
  addSkipNavigation() {
    // Check if skip link already exists
    if (document.querySelector('.skip-link')) {
      return;
    }

    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link';
    skipLink.textContent = 'Skip to main content';

    // Insert at beginning of body
    document.body.insertBefore(skipLink, document.body.firstChild);

    // Ensure main content has ID
    const mainContent = document.querySelector('main') ||
                       document.querySelector('[role="main"]') ||
                       document.querySelector('.container').parentElement;

    if (mainContent && !mainContent.id) {
      mainContent.id = 'main-content';
    }
  }

  /**
   * Improve table accessibility
   * @param {HTMLElement} table - Table element
   */
  enhanceTableAccessibility(table) {
    // Add scope to header cells
    const headers = table.querySelectorAll('thead th');
    headers.forEach(th => {
      if (!th.hasAttribute('scope')) {
        th.setAttribute('scope', 'col');
      }
    });

    // Add row headers if first column contains text
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
      const firstCell = row.querySelector('td:first-child');
      if (firstCell && !firstCell.hasAttribute('scope')) {
        const hasOnlyText = !firstCell.querySelector('input, button, select');
        if (hasOnlyText) {
          firstCell.setAttribute('scope', 'row');
        }
      }
    });

    // Add caption if missing
    if (!table.querySelector('caption') && table.hasAttribute('aria-label')) {
      const caption = document.createElement('caption');
      caption.className = 'visually-hidden';
      caption.textContent = table.getAttribute('aria-label');
      table.insertBefore(caption, table.firstChild);
    }
  }

  /**
   * Add ARIA labels to navigation
   */
  enhanceNavigation() {
    // Main navigation
    const nav = document.querySelector('nav.navbar');
    if (nav && !nav.hasAttribute('aria-label')) {
      nav.setAttribute('aria-label', 'Main navigation');
    }

    // Current page indicator
    const currentLink = document.querySelector('.nav-link.active');
    if (currentLink && !currentLink.hasAttribute('aria-current')) {
      currentLink.setAttribute('aria-current', 'page');
    }
  }

  /**
   * Enhance form accessibility
   * @param {HTMLElement} form - Form element
   */
  enhanceFormAccessibility(form) {
    // Associate labels with inputs
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
      if (!input.id) {
        input.id = `input-${Math.random().toString(36).substr(2, 9)}`;
      }

      // Find associated label
      const label = form.querySelector(`label[for="${input.id}"]`);
      if (!label) {
        // Look for parent label
        const parentLabel = input.closest('label');
        if (parentLabel && !parentLabel.hasAttribute('for')) {
          parentLabel.setAttribute('for', input.id);
        }
      }

      // Add required indicator
      if (input.hasAttribute('required') && !input.hasAttribute('aria-required')) {
        input.setAttribute('aria-required', 'true');
      }
    });

    // Add aria-describedby for error messages
    const errorMessages = form.querySelectorAll('.invalid-feedback');
    errorMessages.forEach(error => {
      const input = error.previousElementSibling;
      if (input && !error.id) {
        error.id = `error-${Math.random().toString(36).substr(2, 9)}`;
        input.setAttribute('aria-describedby', error.id);
      }
    });
  }
}

// Export for module usage
export { AccessibilityManager };

// Auto-initialize for browser usage
if (typeof window !== 'undefined') {
  window.AccessibilityManager = AccessibilityManager;

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      window.a11y = new AccessibilityManager();

      // Add skip navigation
      window.a11y.addSkipNavigation();

      // Enhance navigation
      window.a11y.enhanceNavigation();

      // Enhance all tables
      document.querySelectorAll('table').forEach(table => {
        window.a11y.enhanceTableAccessibility(table);
      });

      // Enhance all forms
      document.querySelectorAll('form').forEach(form => {
        window.a11y.enhanceFormAccessibility(form);
      });
    });
  } else {
    window.a11y = new AccessibilityManager();
    window.a11y.addSkipNavigation();
    window.a11y.enhanceNavigation();
  }
}
