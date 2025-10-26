/**
 * Preview Cycling Module
 * Handles image preview cycling on hover for highlight cards
 */

class PreviewCycler {
  constructor(containerSelector = '.preview-images, .preview-images-small') {
    this.containerSelector = containerSelector;
    this.activeIntervals = new Map();
    this.videoPlayer = null; // Will be set if VideoPlayer is available
  }

  /**
   * Initialize preview cycling for all containers on the page
   * @param {VideoPlayer} videoPlayer - Optional VideoPlayer instance for preloading
   */
  init(videoPlayer = null) {
    this.videoPlayer = videoPlayer;
    const containers = document.querySelectorAll(this.containerSelector);

    containers.forEach(container => {
      this.setupContainer(container);
    });
  }

  /**
   * Set up preview cycling for a single container
   * @param {HTMLElement} container - The preview images container
   */
  setupContainer(container) {
    const images = container.querySelectorAll('.preview-image, .preview-image-small');
    const previewCount = parseInt(container.dataset.previewCount);

    if (previewCount <= 1) {
      return; // No cycling needed for single image
    }

    let currentIndex = 0;
    const parentCard = container.closest('.highlight-card, .highlight-card-small');

    if (!parentCard) return;

    // Extract video URL from onclick attribute if it exists
    const videoUrl = this.extractVideoUrl(parentCard);

    // Mouse enter - start cycling
    parentCard.addEventListener('mouseenter', () => {
      this.startCycling(container, images, previewCount, videoUrl);
    });

    // Mouse leave - stop cycling
    parentCard.addEventListener('mouseleave', () => {
      this.stopCycling(container, images);
    });
  }

  /**
   * Start cycling through preview images
   * @param {HTMLElement} container - The preview container
   * @param {NodeList} images - All preview images
   * @param {number} previewCount - Total number of previews
   * @param {string} videoUrl - Video URL for preloading
   */
  startCycling(container, images, previewCount, videoUrl) {
    let currentIndex = 0;

    const interval = setInterval(() => {
      // Hide current image
      images[currentIndex].classList.remove('active');

      // Move to next image
      currentIndex = (currentIndex + 1) % previewCount;

      // Show next image
      images[currentIndex].classList.add('active');
    }, 800); // Change image every 800ms

    // Store interval for cleanup
    this.activeIntervals.set(container, interval);

    // Preload video after brief delay
    if (videoUrl && this.videoPlayer) {
      setTimeout(() => {
        this.videoPlayer.preload(videoUrl);
      }, 500); // Wait 500ms before preloading
    }
  }

  /**
   * Stop cycling and reset to first image
   * @param {HTMLElement} container - The preview container
   * @param {NodeList} images - All preview images
   */
  stopCycling(container, images) {
    // Clear interval
    const interval = this.activeIntervals.get(container);
    if (interval) {
      clearInterval(interval);
      this.activeIntervals.delete(container);
    }

    // Reset to first image
    images.forEach((img, index) => {
      img.classList.toggle('active', index === 0);
    });
  }

  /**
   * Extract video URL from card's onclick attribute
   * @param {HTMLElement} card - The highlight card element
   * @returns {string|null} The video URL or null
   */
  extractVideoUrl(card) {
    const onclick = card.getAttribute('onclick');
    if (!onclick) return null;

    const match = onclick.match(/'([^']+)'/);
    return match ? match[1] : null;
  }

  /**
   * Clean up all active intervals
   */
  cleanup() {
    this.activeIntervals.forEach(interval => clearInterval(interval));
    this.activeIntervals.clear();
  }

  /**
   * Destroy the preview cycler instance
   */
  destroy() {
    this.cleanup();
  }
}

// Export for use in templates
if (typeof window !== 'undefined') {
  window.PreviewCycler = PreviewCycler;
}
