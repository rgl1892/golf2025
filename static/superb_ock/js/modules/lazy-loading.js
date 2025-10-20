/**
 * Lazy Loading Module
 * Lazy loads images and videos for better performance
 */

class LazyLoader {
  constructor(options = {}) {
    this.options = {
      rootMargin: '50px',  // Start loading 50px before entering viewport
      threshold: 0.01,      // Trigger when 1% visible
      ...options
    };

    this.observer = null;
    this.init();
  }

  /**
   * Initialize lazy loading
   */
  init() {
    if (!('IntersectionObserver' in window)) {
      // Fallback for browsers without IntersectionObserver
      this.loadAllImages();
      return;
    }

    this.observer = new IntersectionObserver(
      (entries) => this.handleIntersection(entries),
      this.options
    );

    this.observe();
  }

  /**
   * Observe all lazy-loadable elements
   */
  observe() {
    // Images with loading="lazy" or data-src
    const lazyImages = document.querySelectorAll('img[loading="lazy"], img[data-src]');
    lazyImages.forEach(img => this.observer.observe(img));

    // Videos with data-src
    const lazyVideos = document.querySelectorAll('video[data-src]');
    lazyVideos.forEach(video => this.observer.observe(video));

    // Background images with data-bg
    const lazyBackgrounds = document.querySelectorAll('[data-bg]');
    lazyBackgrounds.forEach(el => this.observer.observe(el));
  }

  /**
   * Handle intersection changes
   * @param {IntersectionObserverEntry[]} entries
   */
  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        this.loadElement(entry.target);
        this.observer.unobserve(entry.target);
      }
    });
  }

  /**
   * Load an element (image, video, or background)
   * @param {HTMLElement} element
   */
  loadElement(element) {
    if (element.tagName === 'IMG') {
      this.loadImage(element);
    } else if (element.tagName === 'VIDEO') {
      this.loadVideo(element);
    } else if (element.dataset.bg) {
      this.loadBackground(element);
    }
  }

  /**
   * Load an image
   * @param {HTMLImageElement} img
   */
  loadImage(img) {
    const src = img.dataset.src || img.src;
    const srcset = img.dataset.srcset;

    if (!src) return;

    // Create new image to preload
    const tempImg = new Image();

    tempImg.onload = () => {
      img.src = src;
      if (srcset) {
        img.srcset = srcset;
      }
      img.classList.add('lazy-loaded');
      img.removeAttribute('data-src');
      img.removeAttribute('data-srcset');

      // Dispatch loaded event
      img.dispatchEvent(new CustomEvent('lazyloaded', { bubbles: true }));
    };

    tempImg.onerror = () => {
      console.error('Failed to load image:', src);
      img.classList.add('lazy-error');
    };

    tempImg.src = src;
    if (srcset) {
      tempImg.srcset = srcset;
    }
  }

  /**
   * Load a video
   * @param {HTMLVideoElement} video
   */
  loadVideo(video) {
    const sources = video.querySelectorAll('source[data-src]');

    sources.forEach(source => {
      source.src = source.dataset.src;
      source.removeAttribute('data-src');
    });

    if (video.dataset.src) {
      video.src = video.dataset.src;
      video.removeAttribute('data-src');
    }

    video.load();
    video.classList.add('lazy-loaded');

    // Dispatch loaded event
    video.dispatchEvent(new CustomEvent('lazyloaded', { bubbles: true }));
  }

  /**
   * Load background image
   * @param {HTMLElement} element
   */
  loadBackground(element) {
    const bg = element.dataset.bg;

    if (!bg) return;

    // Preload image
    const tempImg = new Image();

    tempImg.onload = () => {
      element.style.backgroundImage = `url('${bg}')`;
      element.classList.add('lazy-loaded');
      element.removeAttribute('data-bg');

      // Dispatch loaded event
      element.dispatchEvent(new CustomEvent('lazyloaded', { bubbles: true }));
    };

    tempImg.onerror = () => {
      console.error('Failed to load background:', bg);
      element.classList.add('lazy-error');
    };

    tempImg.src = bg;
  }

  /**
   * Fallback: Load all images immediately (for unsupported browsers)
   */
  loadAllImages() {
    const lazyElements = document.querySelectorAll('img[data-src], video[data-src], [data-bg]');
    lazyElements.forEach(el => this.loadElement(el));
  }

  /**
   * Manually trigger load for new elements
   * @param {string} selector - CSS selector for elements to observe
   */
  refresh(selector = null) {
    if (selector) {
      const elements = document.querySelectorAll(selector);
      elements.forEach(el => this.observer.observe(el));
    } else {
      this.observe();
    }
  }

  /**
   * Disconnect observer and clean up
   */
  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
}

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.lazyLoader = new LazyLoader();
});

// Export for manual usage
window.LazyLoader = LazyLoader;
