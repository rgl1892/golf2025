/**
 * Accessibility Utilities Module
 * ARIA labels, keyboard navigation, and accessibility helpers
 */

class AccessibilityHelper {
  constructor() {
    this.focusTrapStack = [];
    this.init();
  }

  /**
   * Initialize accessibility features
   */
  init() {
    this.addSkipLink();
    this.setupKeyboardShortcuts();
    this.setupFocusVisible();
  }

  /**
   * Add skip navigation link
   */
  addSkipLink() {
    if (document.getElementById('skip-link')) return; // Already exists

    const skipLink = document.createElement('a');
    skipLink.id = 'skip-link';
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link';
    skipLink.textContent = 'Skip to main content';

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      .skip-link {
        position: absolute;
        top: -40px;
        left: 0;
        background: var(--color-primary, #007bff);
        color: white;
        padding: 8px 16px;
        z-index: 10000;
        text-decoration: none;
        border-radius: 0 0 4px 0;
      }
      .skip-link:focus {
        top: 0;
      }
    `;
    document.head.appendChild(style);

    document.body.insertBefore(skipLink, document.body.firstChild);

    // Ensure main content has ID
    const mainContent = document.querySelector('main, .main, .container');
    if (mainContent && !mainContent.id) {
      mainContent.id = 'main-content';
      mainContent.setAttribute('tabindex', '-1');
    }
  }

  /**
   * Setup keyboard shortcuts
   */
  setupKeyboardShortcuts() {
    this.shortcuts = new Map();

    // Listen for shortcut key
    document.addEventListener('keydown', (e) => {
      // Show keyboard shortcuts help with '?'
      if (e.key === '?' && !this.isInputFocused()) {
        e.preventDefault();
        this.showKeyboardHelp();
      }
    });
  }

  /**
   * Register a keyboard shortcut
   * @param {string} key - The key to listen for
   * @param {Function} callback - Function to call when key is pressed
   * @param {string} description - Description for help modal
   */
  registerShortcut(key, callback, description) {
    this.shortcuts.set(key, { callback, description });

    document.addEventListener('keydown', (e) => {
      if (e.key === key && !this.isInputFocused()) {
        e.preventDefault();
        callback(e);
      }
    });
  }

  /**
   * Check if an input element is focused
   * @returns {boolean}
   */
  isInputFocused() {
    const activeElement = document.activeElement;
    return activeElement && (
      activeElement.tagName === 'INPUT' ||
      activeElement.tagName === 'TEXTAREA' ||
      activeElement.tagName === 'SELECT' ||
      activeElement.isContentEditable
    );
  }

  /**
   * Show keyboard shortcuts help modal
   */
  showKeyboardHelp() {
    if (!this.shortcuts.size) {
      console.log('No keyboard shortcuts registered');
      return;
    }

    let helpHTML = '<div class="keyboard-help-modal">';
    helpHTML += '<div class="keyboard-help-content">';
    helpHTML += '<h4>Keyboard Shortcuts</h4>';
    helpHTML += '<table class="table table-sm">';
    helpHTML += '<thead><tr><th>Key</th><th>Action</th></tr></thead>';
    helpHTML += '<tbody>';

    this.shortcuts.forEach((value, key) => {
      helpHTML += `<tr><td><kbd>${this.formatKey(key)}</kbd></td><td>${value.description}</td></tr>`;
    });

    helpHTML += '</tbody></table>';
    helpHTML += '<p class="text-muted small">Press <kbd>Esc</kbd> to close</p>';
    helpHTML += '</div></div>';

    // Add styles
    const style = document.createElement('style');
    style.id = 'keyboard-help-styles';
    if (!document.getElementById('keyboard-help-styles')) {
      style.textContent = `
        .keyboard-help-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          z-index: 10000;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .keyboard-help-content {
          background: white;
          padding: 2rem;
          border-radius: 8px;
          max-width: 500px;
          max-height: 80vh;
          overflow-y: auto;
        }
        [data-bs-theme="dark"] .keyboard-help-content {
          background: #212529;
          color: #f8f9fa;
        }
        kbd {
          background: #f4f4f4;
          border: 1px solid #ccc;
          border-radius: 3px;
          padding: 2px 6px;
          font-family: monospace;
        }
        [data-bs-theme="dark"] kbd {
          background: #495057;
          border-color: #6c757d;
        }
      `;
      document.head.appendChild(style);
    }

    // Create and show modal
    const modal = document.createElement('div');
    modal.innerHTML = helpHTML;
    document.body.appendChild(modal);

    // Close on Escape or click outside
    const closeHelp = () => {
      modal.remove();
      document.removeEventListener('keydown', escapeHandler);
    };

    const escapeHandler = (e) => {
      if (e.key === 'Escape') {
        closeHelp();
      }
    };

    document.addEventListener('keydown', escapeHandler);
    modal.querySelector('.keyboard-help-modal').addEventListener('click', (e) => {
      if (e.target.classList.contains('keyboard-help-modal')) {
        closeHelp();
      }
    });
  }

  /**
   * Format key for display
   * @param {string} key - Key name
   * @returns {string} - Formatted key
   */
  formatKey(key) {
    const keyMap = {
      'ArrowLeft': '←',
      'ArrowRight': '→',
      'ArrowUp': '↑',
      'ArrowDown': '↓',
      'Escape': 'Esc',
      ' ': 'Space'
    };
    return keyMap[key] || key.toUpperCase();
  }

  /**
   * Setup :focus-visible polyfill for better keyboard navigation
   */
  setupFocusVisible() {
    // Add class to body to enable focus styles only for keyboard navigation
    document.addEventListener('mousedown', () => {
      document.body.classList.add('using-mouse');
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        document.body.classList.remove('using-mouse');
      }
    });

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      /* Only show focus outline when using keyboard */
      .using-mouse *:focus {
        outline: none;
      }

      /* Show clear focus indicators for keyboard navigation */
      *:focus-visible {
        outline: 2px solid var(--color-primary, #007bff);
        outline-offset: 2px;
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Trap focus within an element (for modals)
   * @param {HTMLElement} element - Element to trap focus within
   */
  trapFocus(element) {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (!focusableElements.length) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    };

    element.addEventListener('keydown', handleTabKey);

    // Store for cleanup
    this.focusTrapStack.push({ element, handler: handleTabKey });

    // Focus first element
    firstElement.focus();
  }

  /**
   * Remove focus trap from an element
   * @param {HTMLElement} element - Element to remove focus trap from
   */
  releaseFocus(element) {
    const trap = this.focusTrapStack.find(t => t.element === element);
    if (trap) {
      element.removeEventListener('keydown', trap.handler);
      this.focusTrapStack = this.focusTrapStack.filter(t => t !== trap);
    }
  }

  /**
   * Announce message to screen readers
   * @param {string} message - Message to announce
   * @param {string} priority - 'polite' or 'assertive'
   */
  announce(message, priority = 'polite') {
    let announcer = document.getElementById('sr-announcer');

    if (!announcer) {
      announcer = document.createElement('div');
      announcer.id = 'sr-announcer';
      announcer.setAttribute('role', 'status');
      announcer.setAttribute('aria-live', priority);
      announcer.setAttribute('aria-atomic', 'true');
      announcer.className = 'visually-hidden';
      document.body.appendChild(announcer);
    }

    // Update aria-live if needed
    if (announcer.getAttribute('aria-live') !== priority) {
      announcer.setAttribute('aria-live', priority);
    }

    // Clear and announce
    announcer.textContent = '';
    setTimeout(() => {
      announcer.textContent = message;
    }, 100);
  }
}

// Create global instance
window.a11y = new AccessibilityHelper();

// Export class
window.AccessibilityHelper = AccessibilityHelper;
