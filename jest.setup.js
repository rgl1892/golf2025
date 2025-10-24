// Add custom jest matchers from jest-dom
import '@testing-library/jest-dom';

// Mock Bootstrap modal if not available
global.bootstrap = {
  Modal: class MockModal {
    constructor(element) {
      this.element = element;
      this._isShown = false;
    }

    show() {
      this._isShown = true;
      this.element.classList.add('show');
      this.element.dispatchEvent(new Event('shown.bs.modal'));
    }

    hide() {
      this._isShown = false;
      this.element.classList.remove('show');
      this.element.dispatchEvent(new Event('hidden.bs.modal'));
    }

    dispose() {
      this.element = null;
    }
  }
};

// Mock console methods to reduce test noise
global.console = {
  ...console,
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  info: jest.fn(),
  debug: jest.fn()
};

// Mock IntersectionObserver for lazy loading tests
global.IntersectionObserver = class IntersectionObserver {
  constructor(callback) {
    this.callback = callback;
  }

  observe() {
    // Mock implementation
  }

  unobserve() {
    // Mock implementation
  }

  disconnect() {
    // Mock implementation
  }
};

// Mock requestAnimationFrame
global.requestAnimationFrame = (callback) => {
  setTimeout(callback, 0);
};

// Mock performance API
if (typeof performance === 'undefined') {
  global.performance = {
    now: () => Date.now(),
    mark: () => {},
    measure: () => {},
    getEntriesByType: () => [],
    getEntriesByName: () => []
  };
}
