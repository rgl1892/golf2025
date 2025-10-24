/**
 * Keyboard Shortcuts Module
 * Displays a help modal with all available keyboard shortcuts
 */

class KeyboardShortcuts {
  constructor() {
    this.shortcuts = [];
    this.modal = null;
    this.isInputFocused = false;
    this.init();
  }

  /**
   * Initialize keyboard shortcuts system
   */
  init() {
    this.registerDefaultShortcuts();
    this.setupEventListeners();
    this.createModal();
  }

  /**
   * Register default keyboard shortcuts
   */
  registerDefaultShortcuts() {
    // Navigation shortcuts
    this.addShortcut('?', 'Show this help menu', 'Navigation');
    this.addShortcut('←, A', 'Previous round', 'Navigation');
    this.addShortcut('→, D', 'Next round', 'Navigation');
    this.addShortcut('Esc', 'Close modal/dialog', 'Navigation');

    // Page shortcuts
    this.addShortcut('H', 'Go to Homepage', 'Pages');
    this.addShortcut('R', 'View Rounds', 'Pages');
    this.addShortcut('L', 'View Highlights', 'Pages');
    this.addShortcut('S', 'View Statistics', 'Pages');

    // Video shortcuts
    this.addShortcut('Space', 'Play/Pause video', 'Video');
    this.addShortcut('F', 'Fullscreen video', 'Video');
    this.addShortcut('M', 'Mute/Unmute video', 'Video');
  }

  /**
   * Add a keyboard shortcut to the registry
   * @param {string} keys - Key combination (e.g., 'Ctrl+S', '?')
   * @param {string} description - What the shortcut does
   * @param {string} category - Category for organization
   */
  addShortcut(keys, description, category = 'General') {
    this.shortcuts.push({ keys, description, category });
  }

  /**
   * Set up event listeners for keyboard shortcuts
   */
  setupEventListeners() {
    document.addEventListener('keydown', (e) => {
      // Check if user is typing in an input field
      this.isInputFocused = ['INPUT', 'TEXTAREA', 'SELECT'].includes(
        document.activeElement.tagName
      );

      // Show help modal on '?' key (Shift+/)
      if (e.key === '?' && !this.isInputFocused) {
        e.preventDefault();
        this.showModal();
      }

      // Page navigation shortcuts (only if not in input)
      if (!this.isInputFocused && !e.ctrlKey && !e.metaKey) {
        this.handlePageShortcuts(e);
      }
    });
  }

  /**
   * Handle page navigation shortcuts
   * @param {KeyboardEvent} e - Keyboard event
   */
  handlePageShortcuts(e) {
    const shortcuts = {
      'h': '/',
      'r': '/rounds',
      'l': '/highlights/',
      's': '/heatmap/'
    };

    const key = e.key.toLowerCase();
    if (shortcuts[key]) {
      e.preventDefault();
      window.location.href = shortcuts[key];
    }
  }

  /**
   * Create the keyboard shortcuts modal
   */
  createModal() {
    // Check if modal already exists
    if (document.getElementById('keyboardShortcutsModal')) {
      return;
    }

    const modalHTML = `
      <div class="modal fade" id="keyboardShortcutsModal" tabindex="-1" aria-labelledby="keyboardShortcutsModalTitle" aria-hidden="true">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="keyboardShortcutsModalTitle">
                <i class="fas fa-keyboard me-2"></i>Keyboard Shortcuts
              </h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              ${this.generateShortcutsHTML()}
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            </div>
          </div>
        </div>
      </div>
    `;

    // Add modal to document
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Store modal reference
    const modalElement = document.getElementById('keyboardShortcutsModal');
    this.modal = new bootstrap.Modal(modalElement);

    // Add styles
    this.injectStyles();
  }

  /**
   * Generate HTML for shortcuts organized by category
   * @returns {string} HTML string
   */
  generateShortcutsHTML() {
    // Group shortcuts by category
    const categories = {};
    this.shortcuts.forEach(shortcut => {
      if (!categories[shortcut.category]) {
        categories[shortcut.category] = [];
      }
      categories[shortcut.category].push(shortcut);
    });

    // Generate HTML for each category
    let html = '<div class="shortcuts-container">';

    Object.keys(categories).forEach(category => {
      html += `
        <div class="shortcut-category mb-4">
          <h6 class="text-muted mb-3">${category}</h6>
          <div class="row g-2">
      `;

      categories[category].forEach(shortcut => {
        html += `
          <div class="col-md-6">
            <div class="shortcut-item">
              <kbd class="shortcut-keys">${this.formatKeys(shortcut.keys)}</kbd>
              <span class="shortcut-description">${shortcut.description}</span>
            </div>
          </div>
        `;
      });

      html += `
          </div>
        </div>
      `;
    });

    html += '</div>';
    return html;
  }

  /**
   * Format key combinations for display
   * @param {string} keys - Key combination string
   * @returns {string} Formatted HTML
   */
  formatKeys(keys) {
    return keys.split(', ').map(key => {
      return `<span class="key">${key}</span>`;
    }).join(' or ');
  }

  /**
   * Inject CSS styles for shortcuts modal
   */
  injectStyles() {
    if (document.getElementById('keyboard-shortcuts-styles')) {
      return;
    }

    const style = document.createElement('style');
    style.id = 'keyboard-shortcuts-styles';
    style.textContent = `
      .shortcuts-container {
        padding: 0;
      }

      .shortcut-category h6 {
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
      }

      .shortcut-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 12px;
        background: var(--bs-light);
        border-radius: 6px;
        transition: background-color 0.2s;
      }

      .shortcut-item:hover {
        background: var(--bs-secondary-bg);
      }

      .shortcut-keys {
        min-width: 100px;
        flex-shrink: 0;
      }

      .shortcut-keys .key {
        background: white;
        border: 1px solid var(--bs-border-color);
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.875rem;
        font-weight: 500;
        box-shadow: 0 2px 0 rgba(0, 0, 0, 0.1);
        display: inline-block;
      }

      .shortcut-description {
        color: var(--bs-body-color);
        font-size: 0.9rem;
      }

      /* Dark mode support */
      [data-bs-theme="dark"] .shortcut-item {
        background: rgba(255, 255, 255, 0.05);
      }

      [data-bs-theme="dark"] .shortcut-item:hover {
        background: rgba(255, 255, 255, 0.1);
      }

      [data-bs-theme="dark"] .shortcut-keys .key {
        background: rgba(0, 0, 0, 0.3);
        border-color: rgba(255, 255, 255, 0.2);
      }
    `;

    document.head.appendChild(style);
  }

  /**
   * Show the keyboard shortcuts modal
   */
  showModal() {
    if (this.modal) {
      this.modal.show();
    }
  }

  /**
   * Hide the keyboard shortcuts modal
   */
  hideModal() {
    if (this.modal) {
      this.modal.hide();
    }
  }

  /**
   * Check if an input element is focused
   * @returns {boolean}
   */
  isInputActive() {
    return this.isInputFocused;
  }
}

// Export for module usage
export { KeyboardShortcuts };

// Auto-initialize for browser usage
if (typeof window !== 'undefined') {
  window.KeyboardShortcuts = KeyboardShortcuts;

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      window.keyboardShortcuts = new KeyboardShortcuts();
    });
  } else {
    window.keyboardShortcuts = new KeyboardShortcuts();
  }
}
