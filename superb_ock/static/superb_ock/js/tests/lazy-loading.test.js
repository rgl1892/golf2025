/**
 * Lazy Loading Tests
 *
 * Tests for the LazyLoader module
 */

import { LazyLoader } from '../modules/lazy-loading.js';

describe('LazyLoader', () => {
  let lazyLoader;

  beforeEach(() => {
    document.body.innerHTML = '';
    lazyLoader = new LazyLoader();
  });

  afterEach(() => {
    if (lazyLoader) {
      lazyLoader.destroy();
    }
  });

  describe('Initialization', () => {
    test('creates IntersectionObserver instance', () => {
      expect(lazyLoader.observer).toBeDefined();
    });

    test('observes images with data-src attribute', () => {
      document.body.innerHTML = `
        <img data-src="/image1.jpg" alt="Test 1">
        <img data-src="/image2.jpg" alt="Test 2">
        <img src="/loaded.jpg" alt="Already loaded">
      `;

      const loader = new LazyLoader();

      // In tests, images load immediately due to mock
      const images = document.querySelectorAll('img[data-src]');
      images.forEach(img => {
        expect(img.src).toContain(img.getAttribute('data-src'));
      });

      loader.destroy();
    });

    test('observes videos with data-src attribute', () => {
      document.body.innerHTML = `
        <video data-src="/video.mp4"></video>
      `;

      const loader = new LazyLoader();

      const video = document.querySelector('video');
      expect(video.src).toContain('/video.mp4');

      loader.destroy();
    });

    test('observes background images with data-bg attribute', () => {
      document.body.innerHTML = `
        <div data-bg="/background.jpg"></div>
      `;

      const loader = new LazyLoader();

      const div = document.querySelector('div');
      expect(div.style.backgroundImage).toContain('/background.jpg');

      loader.destroy();
    });
  });

  describe('Image loading', () => {
    test('loads image when intersecting', () => {
      document.body.innerHTML = `
        <img data-src="/test.jpg" alt="Test">
      `;

      const loader = new LazyLoader();
      const img = document.querySelector('img');

      expect(img.src).toContain('/test.jpg');
      expect(img.hasAttribute('data-src')).toBe(false);

      loader.destroy();
    });

    test('handles srcset attribute', () => {
      document.body.innerHTML = `
        <img data-src="/test.jpg"
             data-srcset="/test-small.jpg 400w, /test-large.jpg 800w"
             alt="Test">
      `;

      const loader = new LazyLoader();
      const img = document.querySelector('img');

      expect(img.srcset).toBe('/test-small.jpg 400w, /test-large.jpg 800w');
      expect(img.hasAttribute('data-srcset')).toBe(false);

      loader.destroy();
    });

    test('adds loaded class to image', () => {
      document.body.innerHTML = `
        <img data-src="/test.jpg" alt="Test">
      `;

      const loader = new LazyLoader();
      const img = document.querySelector('img');

      // Simulate image load
      img.dispatchEvent(new Event('load'));

      expect(img).toHaveClass('lazy-loaded');

      loader.destroy();
    });
  });

  describe('Video loading', () => {
    test('loads video source when intersecting', () => {
      document.body.innerHTML = `
        <video data-src="/video.mp4">
          <source data-src="/video.mp4" type="video/mp4">
        </video>
      `;

      const loader = new LazyLoader();
      const video = document.querySelector('video');

      expect(video.src).toContain('/video.mp4');

      loader.destroy();
    });

    test('loads video poster', () => {
      document.body.innerHTML = `
        <video data-src="/video.mp4" data-poster="/poster.jpg"></video>
      `;

      const loader = new LazyLoader();
      const video = document.querySelector('video');

      expect(video.poster).toContain('/poster.jpg');

      loader.destroy();
    });
  });

  describe('Background image loading', () => {
    test('sets background image from data-bg', () => {
      document.body.innerHTML = `
        <div data-bg="/background.jpg"></div>
      `;

      const loader = new LazyLoader();
      const div = document.querySelector('div');

      expect(div.style.backgroundImage).toContain('/background.jpg');
      expect(div.hasAttribute('data-bg')).toBe(false);

      loader.destroy();
    });

    test('adds loaded class to background element', () => {
      document.body.innerHTML = `
        <div data-bg="/background.jpg"></div>
      `;

      const loader = new LazyLoader();
      const div = document.querySelector('div');

      expect(div).toHaveClass('lazy-loaded');

      loader.destroy();
    });
  });

  describe('Observer management', () => {
    test('unobserves element after loading', () => {
      document.body.innerHTML = `
        <img data-src="/test.jpg" alt="Test">
      `;

      const loader = new LazyLoader();
      const img = document.querySelector('img');

      // After loading, data-src should be removed
      expect(img.hasAttribute('data-src')).toBe(false);

      loader.destroy();
    });

    test('disconnect stops observing', () => {
      const loader = new LazyLoader();
      const disconnectSpy = jest.spyOn(loader.observer, 'disconnect');

      loader.destroy();

      expect(disconnectSpy).toHaveBeenCalled();
    });
  });

  describe('Dynamic content', () => {
    test('observes newly added elements', () => {
      const loader = new LazyLoader();

      // Add new image
      const img = document.createElement('img');
      img.setAttribute('data-src', '/dynamic.jpg');
      img.alt = 'Dynamic';
      document.body.appendChild(img);

      loader.observeNewElements();

      expect(img.src).toContain('/dynamic.jpg');

      loader.destroy();
    });
  });

  describe('Error handling', () => {
    test('handles missing data-src gracefully', () => {
      document.body.innerHTML = `
        <img alt="No source">
      `;

      expect(() => {
        const loader = new LazyLoader();
        loader.destroy();
      }).not.toThrow();
    });

    test('handles invalid URLs', () => {
      document.body.innerHTML = `
        <img data-src="" alt="Empty source">
      `;

      expect(() => {
        const loader = new LazyLoader();
        loader.destroy();
      }).not.toThrow();
    });

    test('continues loading other elements if one fails', () => {
      document.body.innerHTML = `
        <img data-src="/valid1.jpg" alt="Valid 1">
        <img data-src="" alt="Invalid">
        <img data-src="/valid2.jpg" alt="Valid 2">
      `;

      const loader = new LazyLoader();

      const validImages = document.querySelectorAll('img[alt^="Valid"]');
      validImages.forEach(img => {
        expect(img.src).toBeTruthy();
      });

      loader.destroy();
    });
  });

  describe('Performance', () => {
    test('uses proper IntersectionObserver options', () => {
      const customLoader = new LazyLoader({
        rootMargin: '100px',
        threshold: 0.5
      });

      expect(customLoader.observer).toBeDefined();

      customLoader.destroy();
    });
  });
});
