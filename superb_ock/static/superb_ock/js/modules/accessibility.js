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

    // Register common shortcuts
    this.registerCommonShortcuts();

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
   * Register common application shortcuts automatically
   */
  registerCommonShortcuts() {
    // Register '?' for help
    this.shortcuts.set('?', {
      callback: () => this.showKeyboardHelp(),
      description: 'Show keyboard shortcuts'
    });

    // Register 'Esc' for closing modals
    this.shortcuts.set('Escape', {
      callback: () => {},
      description: 'Close modal/dialog'
    });

    // Detect round navigation buttons and register A/D shortcuts
    const prevButton = document.querySelector('[href*="previous"]');
    const nextButton = document.querySelector('[href*="next"]');

    if (prevButton || nextButton) {
      if (prevButton) {
        this.registerShortcut('a', () => prevButton.click(), 'Previous round');
        this.registerShortcut('ArrowLeft', () => prevButton.click(), 'Previous round');
      }

      if (nextButton) {
        this.registerShortcut('d', () => nextButton.click(), 'Next round');
        this.registerShortcut('ArrowRight', () => nextButton.click(), 'Next round');
      }
    }

    // Detect home link
    const homeLink = document.querySelector('[href="/"]');
    if (homeLink) {
      this.registerShortcut('h', () => homeLink.click(), 'Go to home');
    }

    // Detect search functionality
    const searchInput = document.querySelector('input[type="search"]');
    if (searchInput) {
      this.registerShortcut('/', (e) => {
        e.preventDefault();
        searchInput.focus();
      }, 'Focus search');
    }
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

    // Group shortcuts by category
    const groups = {
      'Navigation': ['h', 'a', 'd', 'ArrowLeft', 'ArrowRight'],
      'General': ['?', 'Escape', '/'],
      'Other': []
    };

    // Organize shortcuts into groups
    const organized = {
      'Navigation': [],
      'General': [],
      'Other': []
    };

    this.shortcuts.forEach((value, key) => {
      let placed = false;
      for (const [groupName, keys] of Object.entries(groups)) {
        if (keys.includes(key)) {
          organized[groupName].push({ key, ...value });
          placed = true;
          break;
        }
      }
      if (!placed) {
        organized['Other'].push({ key, ...value });
      }
    });

    let helpHTML = '<div class="keyboard-help-modal" role="dialog" aria-labelledby="keyboard-help-title" aria-modal="true">';
    helpHTML += '<div class="keyboard-help-content">';
    helpHTML += '<div class="keyboard-help-header">';
    helpHTML += '<h4 id="keyboard-help-title"><i class="fas fa-keyboard me-2"></i>Keyboard Shortcuts</h4>';
    helpHTML += '<button class="keyboard-help-close" aria-label="Close keyboard shortcuts">&times;</button>';
    helpHTML += '</div>';

    // Add groups
    for (const [groupName, shortcuts] of Object.entries(organized)) {
      if (shortcuts.length === 0) continue;

      helpHTML += `<div class="keyboard-help-group">`;
      helpHTML += `<h5 class="keyboard-help-group-title">${groupName}</h5>`;
      helpHTML += '<table class="table table-sm table-borderless">';
      helpHTML += '<tbody>';

      shortcuts.forEach(({ key, description }) => {
        helpHTML += `<tr>`;
        helpHTML += `<td class="text-end"><kbd>${this.formatKey(key)}</kbd></td>`;
        helpHTML += `<td>${description}</td>`;
        helpHTML += `</tr>`;
      });

      helpHTML += '</tbody></table>';
      helpHTML += '</div>';
    }

    helpHTML += '<div class="keyboard-help-footer">';
    helpHTML += '<p class="text-muted small mb-0"><i class="fas fa-info-circle me-1"></i>Press <kbd>Esc</kbd> or click outside to close</p>';
    helpHTML += '</div>';
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
          backdrop-filter: blur(4px);
          z-index: 10000;
          display: flex;
          align-items: center;
          justify-content: center;
          animation: fadeIn 0.2s ease-out;
          padding: 1rem;
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        .keyboard-help-content {
          background: white;
          border-radius: 12px;
          max-width: 600px;
          width: 100%;
          max-height: 80vh;
          overflow-y: auto;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
          animation: slideUp 0.3s ease-out;
        }
        @keyframes slideUp {
          from {
            transform: translateY(30px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        [data-bs-theme="dark"] .keyboard-help-content {
          background: #212529;
          color: #f8f9fa;
        }
        .keyboard-help-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem 2rem 1rem;
          border-bottom: 1px solid #dee2e6;
        }
        [data-bs-theme="dark"] .keyboard-help-header {
          border-bottom-color: #495057;
        }
        .keyboard-help-header h4 {
          margin: 0;
          font-size: 1.5rem;
          font-weight: 600;
        }
        .keyboard-help-close {
          background: none;
          border: none;
          font-size: 2rem;
          line-height: 1;
          color: #6c757d;
          cursor: pointer;
          padding: 0;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
          transition: background-color 0.2s, color 0.2s;
        }
        .keyboard-help-close:hover {
          background-color: #f8f9fa;
          color: #212529;
        }
        [data-bs-theme="dark"] .keyboard-help-close:hover {
          background-color: #343a40;
          color: #f8f9fa;
        }
        .keyboard-help-group {
          padding: 1.5rem 2rem;
          border-bottom: 1px solid #f0f0f0;
        }
        [data-bs-theme="dark"] .keyboard-help-group {
          border-bottom-color: #343a40;
        }
        .keyboard-help-group:last-of-type {
          border-bottom: none;
        }
        .keyboard-help-group-title {
          font-size: 0.875rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: #6c757d;
          margin: 0 0 1rem 0;
        }
        .keyboard-help-group table {
          margin: 0;
        }
        .keyboard-help-group td {
          padding: 0.5rem 0;
        }
        .keyboard-help-group td:first-child {
          padding-right: 1rem;
          width: 100px;
        }
        kbd {
          background: #f4f4f4;
          border: 1px solid #d0d0d0;
          border-bottom-width: 2px;
          border-radius: 4px;
          padding: 4px 8px;
          font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
          font-size: 0.875rem;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
          display: inline-block;
          min-width: 24px;
          text-align: center;
        }
        [data-bs-theme="dark"] kbd {
          background: #495057;
          border-color: #6c757d;
          color: #f8f9fa;
        }
        .keyboard-help-footer {
          padding: 1rem 2rem;
          background-color: #f8f9fa;
          border-radius: 0 0 12px 12px;
        }
        [data-bs-theme="dark"] .keyboard-help-footer {
          background-color: #1a1d20;
        }
        @media (max-width: 768px) {
          .keyboard-help-content {
            max-width: 100%;
            max-height: 90vh;
          }
          .keyboard-help-header,
          .keyboard-help-group,
          .keyboard-help-footer {
            padding-left: 1.5rem;
            padding-right: 1.5rem;
          }
        }
      `;
      document.head.appendChild(style);
    }

    // Create and show modal
    const modal = document.createElement('div');
    modal.innerHTML = helpHTML;
    document.body.appendChild(modal);

    // Trap focus in modal
    this.trapFocus(modal.querySelector('.keyboard-help-content'));

    // Close on Escape or click outside
    const closeHelp = () => {
      this.releaseFocus(modal.querySelector('.keyboard-help-content'));
      modal.remove();
      document.removeEventListener('keydown', escapeHandler);
    };

    const escapeHandler = (e) => {
      if (e.key === 'Escape') {
        closeHelp();
      }
    };

    document.addEventListener('keydown', escapeHandler);

    // Close button handler
    modal.querySelector('.keyboard-help-close').addEventListener('click', closeHelp);

    // Click outside to close
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
