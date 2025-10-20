/**
 * Jest Test Setup
 *
 * This file runs before all tests and sets up the testing environment.
 * It configures testing-library/jest-dom matchers and mocks global objects.
 */

import '@testing-library/jest-dom';

// Mock Bootstrap Modal
global.bootstrap = {
  Modal: class {
    constructor(element) {
      this.element = element;
      this._isShown = false;
    }
    show() {
      this._isShown = true;
      this.element.classList.add('show');
      this.element.style.display = 'block';
      const event = new Event('shown.bs.modal');
      this.element.dispatchEvent(event);
    }
    hide() {
      this._isShown = false;
      this.element.classList.remove('show');
      this.element.style.display = 'none';
      const event = new Event('hidden.bs.modal');
      this.element.dispatchEvent(event);
    }
  }
};

// Mock window.toast for toast notification tests
global.toast = {
  success: jest.fn(),
  error: jest.fn(),
  warning: jest.fn(),
  info: jest.fn()
};

// Mock IntersectionObserver for lazy loading tests
global.IntersectionObserver = class IntersectionObserver {
  constructor(callback) {
    this.callback = callback;
    this.observedElements = new Set();
  }
  observe(element) {
    this.observedElements.add(element);
    // Simulate immediate intersection for tests
    this.callback([{ isIntersecting: true, target: element }]);
  }
  unobserve(element) {
    this.observedElements.delete(element);
  }
  disconnect() {
    this.observedElements.clear();
  }
};

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
global.localStorage = localStorageMock;

// Mock scrollIntoView
Element.prototype.scrollIntoView = jest.fn();

// Suppress console errors in tests (optional)
// global.console.error = jest.fn();
// global.console.warn = jest.fn();
