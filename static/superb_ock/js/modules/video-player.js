/**
 * Video Player Module
 * Handles video modal playback and preloading
 */

class VideoPlayer {
  constructor(videoId, modalId, modalTitleId) {
    this.video = document.getElementById(videoId);
    this.modalElement = document.getElementById(modalId);
    this.modalTitle = document.getElementById(modalTitleId);
    this.modal = null;
    this.preloadedVideos = new Set();

    // Initialize Bootstrap modal if element exists
    if (this.modalElement && typeof bootstrap !== 'undefined') {
      this.modal = new bootstrap.Modal(this.modalElement);
      this.setupEventListeners();
    }
  }

  /**
   * Set up event listeners for modal cleanup
   */
  setupEventListeners() {
    this.modalElement.addEventListener('hidden.bs.modal', () => {
      this.cleanup();
    });
  }

  /**
   * Play a video in the modal
   * @param {string} videoUrl - URL of the video to play
   * @param {string} title - Title to display in modal header
   * @param {string} context - Additional context (e.g., "Hole 3")
   */
  play(videoUrl, title = 'Golf Highlight', context = '') {
    if (!this.video || !this.modal) {
      console.error('Video player not properly initialized');
      return;
    }

    // Show loading state
    this.video.style.opacity = '0.7';

    // Set video source and metadata
    this.video.src = videoUrl;
    this.video.load();

    // Update modal title
    const fullTitle = context ? `${title} - ${context}` : title;
    if (this.modalTitle) {
      this.modalTitle.textContent = fullTitle;
    }

    // Show modal
    this.modal.show();

    // Handle video loading events
    this.handleVideoLoading();
  }

  /**
   * Handle video loading events
   */
  handleVideoLoading() {
    // Loading started
    this.video.addEventListener('loadstart', () => {
      console.log('Video loading started...');
    }, { once: true });

    // Video ready to play
    this.video.addEventListener('canplay', () => {
      this.video.style.opacity = '1';
      // Optionally auto-play when ready
      // this.video.play();
    }, { once: true });

    // Handle errors
    this.video.addEventListener('error', (e) => {
      console.error('Video loading error:', e);
      this.video.style.opacity = '1';
      // Could show error message to user here
    }, { once: true });
  }

  /**
   * Preload a video for faster playback
   * @param {string} videoUrl - URL of the video to preload
   */
  preload(videoUrl) {
    if (this.preloadedVideos.has(videoUrl)) {
      return; // Already preloaded
    }

    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'video';
    link.href = videoUrl;
    link.setAttribute('crossorigin', 'anonymous');
    document.head.appendChild(link);

    this.preloadedVideos.add(videoUrl);
    console.log('Preloading video:', videoUrl);
  }

  /**
   * Clean up video resources
   */
  cleanup() {
    if (this.video) {
      this.video.pause();
      this.video.currentTime = 0;
      this.video.src = ''; // Clear source to free memory
    }
  }

  /**
   * Destroy the video player instance
   */
  destroy() {
    this.cleanup();
    if (this.modal) {
      this.modal.dispose();
    }
  }
}

// Export for use in templates
window.VideoPlayer = VideoPlayer;
