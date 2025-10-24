/**
 * Tests for PreviewCycler Module
 */

import { PreviewCycler } from '../superb_ock/static/superb_ock/js/modules/preview-cycling.js';

// Mock VideoPlayer
const mockVideoPlayer = {
  preload: jest.fn()
};

describe('PreviewCycler', () => {
  let cycler;

  beforeEach(() => {
    // Clear mocks
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useFakeTimers();

    // Set up DOM
    document.body.innerHTML = `
      <div class="highlight-card" onclick="playVideo('https://example.com/video.mp4')">
        <div class="preview-images" data-preview-count="3">
          <img class="preview-image active" src="preview1.jpg" alt="Preview 1">
          <img class="preview-image" src="preview2.jpg" alt="Preview 2">
          <img class="preview-image" src="preview3.jpg" alt="Preview 3">
        </div>
      </div>
    `;

    cycler = new PreviewCycler();
  });

  afterEach(() => {
    if (cycler) {
      cycler.cleanup();
    }
    document.body.innerHTML = '';
    jest.useRealTimers();
  });

  describe('Initialization', () => {
    test('initializes with default container selector', () => {
      expect(cycler.containerSelector).toBe('.preview-images, .preview-images-small');
    });

    test('initializes empty intervals map', () => {
      expect(cycler.activeIntervals).toBeInstanceOf(Map);
      expect(cycler.activeIntervals.size).toBe(0);
    });

    test('accepts custom container selector', () => {
      const customCycler = new PreviewCycler('.custom-selector');
      expect(customCycler.containerSelector).toBe('.custom-selector');
    });

    test('videoPlayer is initially null', () => {
      expect(cycler.videoPlayer).toBeNull();
    });
  });

  describe('init() method', () => {
    test('sets up all preview containers', () => {
      cycler.init();

      const container = document.querySelector('.preview-images');
      const card = container.closest('.highlight-card');

      expect(card).toBeDefined();
    });

    test('stores video player reference', () => {
      cycler.init(mockVideoPlayer);
      expect(cycler.videoPlayer).toBe(mockVideoPlayer);
    });

    test('handles multiple containers', () => {
      document.body.innerHTML = `
        <div class="highlight-card">
          <div class="preview-images" data-preview-count="2">
            <img class="preview-image active" src="1.jpg">
            <img class="preview-image" src="2.jpg">
          </div>
        </div>
        <div class="highlight-card">
          <div class="preview-images" data-preview-count="2">
            <img class="preview-image active" src="3.jpg">
            <img class="preview-image" src="4.jpg">
          </div>
        </div>
      `;

      cycler.init();

      const containers = document.querySelectorAll('.preview-images');
      expect(containers.length).toBe(2);
    });
  });

  describe('setupContainer() method', () => {
    test('skips setup for single image', () => {
      document.body.innerHTML = `
        <div class="highlight-card">
          <div class="preview-images" data-preview-count="1">
            <img class="preview-image active" src="1.jpg">
          </div>
        </div>
      `;

      const container = document.querySelector('.preview-images');
      cycler.setupContainer(container);

      // Should not add any event listeners
      expect(cycler.activeIntervals.size).toBe(0);
    });

    test('returns early if no parent card', () => {
      document.body.innerHTML = `
        <div class="preview-images" data-preview-count="3">
          <img class="preview-image active" src="1.jpg">
          <img class="preview-image" src="2.jpg">
          <img class="preview-image" src="3.jpg">
        </div>
      `;

      const container = document.querySelector('.preview-images');
      expect(() => {
        cycler.setupContainer(container);
      }).not.toThrow();
    });

    test('adds mouseenter listener', () => {
      const container = document.querySelector('.preview-images');
      cycler.setupContainer(container);

      const card = container.closest('.highlight-card');

      // Trigger mouseenter
      card.dispatchEvent(new Event('mouseenter'));

      // Should create an interval
      expect(cycler.activeIntervals.size).toBe(1);
    });

    test('adds mouseleave listener', () => {
      const container = document.querySelector('.preview-images');
      cycler.setupContainer(container);

      const card = container.closest('.highlight-card');

      // Start cycling
      card.dispatchEvent(new Event('mouseenter'));
      expect(cycler.activeIntervals.size).toBe(1);

      // Stop cycling
      card.dispatchEvent(new Event('mouseleave'));
      expect(cycler.activeIntervals.size).toBe(0);
    });
  });

  describe('startCycling() method', () => {
    test('creates interval for cycling', () => {
      const container = document.querySelector('.preview-images');
      const images = container.querySelectorAll('.preview-image');

      cycler.startCycling(container, images, 3, null);

      expect(cycler.activeIntervals.has(container)).toBe(true);
    });

    test('cycles through images', () => {
      const container = document.querySelector('.preview-images');
      const images = container.querySelectorAll('.preview-image');

      cycler.startCycling(container, images, 3, null);

      // Initially first image is active
      expect(images[0]).toHaveClass('active');
      expect(images[1]).not.toHaveClass('active');

      // Advance time by 800ms
      jest.advanceTimersByTime(800);

      // Second image should be active
      expect(images[0]).not.toHaveClass('active');
      expect(images[1]).toHaveClass('active');

      // Advance another 800ms
      jest.advanceTimersByTime(800);

      // Third image should be active
      expect(images[1]).not.toHaveClass('active');
      expect(images[2]).toHaveClass('active');

      // Advance another 800ms
      jest.advanceTimersByTime(800);

      // Should cycle back to first image
      expect(images[2]).not.toHaveClass('active');
      expect(images[0]).toHaveClass('active');
    });

    test('preloads video after delay', () => {
      const container = document.querySelector('.preview-images');
      const images = container.querySelectorAll('.preview-image');
      const videoUrl = 'https://example.com/video.mp4';

      cycler.videoPlayer = mockVideoPlayer;
      cycler.startCycling(container, images, 3, videoUrl);

      // Preload should not be called immediately
      expect(mockVideoPlayer.preload).not.toHaveBeenCalled();

      // Advance time by 500ms
      jest.advanceTimersByTime(500);

      // Preload should be called
      expect(mockVideoPlayer.preload).toHaveBeenCalledWith(videoUrl);
    });

    test('does not preload if no video URL', () => {
      const container = document.querySelector('.preview-images');
      const images = container.querySelectorAll('.preview-image');

      cycler.videoPlayer = mockVideoPlayer;
      cycler.startCycling(container, images, 3, null);

      jest.advanceTimersByTime(1000);

      expect(mockVideoPlayer.preload).not.toHaveBeenCalled();
    });

    test('does not preload if no video player', () => {
      const container = document.querySelector('.preview-images');
      const images = container.querySelectorAll('.preview-image');

      cycler.startCycling(container, images, 3, 'https://example.com/video.mp4');

      jest.advanceTimersByTime(1000);

      // Should not throw
      expect(mockVideoPlayer.preload).not.toHaveBeenCalled();
    });
  });

  describe('stopCycling() method', () => {
    test('clears interval', () => {
      const container = document.querySelector('.preview-images');
      const images = container.querySelectorAll('.preview-image');

      cycler.startCycling(container, images, 3, null);
      expect(cycler.activeIntervals.has(container)).toBe(true);

      cycler.stopCycling(container, images);
      expect(cycler.activeIntervals.has(container)).toBe(false);
    });

    test('resets to first image', () => {
      const container = document.querySelector('.preview-images');
      const images = container.querySelectorAll('.preview-image');

      cycler.startCycling(container, images, 3, null);

      // Advance to second image
      jest.advanceTimersByTime(800);
      expect(images[1]).toHaveClass('active');

      cycler.stopCycling(container, images);

      // Should reset to first image
      expect(images[0]).toHaveClass('active');
      expect(images[1]).not.toHaveClass('active');
    });

    test('handles non-existent interval gracefully', () => {
      const container = document.querySelector('.preview-images');
      const images = container.querySelectorAll('.preview-image');

      expect(() => {
        cycler.stopCycling(container, images);
      }).not.toThrow();
    });
  });

  describe('extractVideoUrl() method', () => {
    test('extracts URL from onclick attribute', () => {
      const card = document.querySelector('.highlight-card');
      const url = cycler.extractVideoUrl(card);

      expect(url).toBe('https://example.com/video.mp4');
    });

    test('returns null if no onclick', () => {
      const card = document.createElement('div');
      const url = cycler.extractVideoUrl(card);

      expect(url).toBeNull();
    });

    test('returns null if onclick does not match pattern', () => {
      const card = document.createElement('div');
      card.setAttribute('onclick', 'someFunction()');
      const url = cycler.extractVideoUrl(card);

      expect(url).toBeNull();
    });
  });

  describe('cleanup() method', () => {
    test('clears all intervals', () => {
      const container = document.querySelector('.preview-images');
      const images = container.querySelectorAll('.preview-image');

      cycler.startCycling(container, images, 3, null);
      expect(cycler.activeIntervals.size).toBe(1);

      cycler.cleanup();
      expect(cycler.activeIntervals.size).toBe(0);
    });

    test('handles empty intervals map', () => {
      expect(() => {
        cycler.cleanup();
      }).not.toThrow();
    });
  });

  describe('destroy() method', () => {
    test('calls cleanup', () => {
      const cleanupSpy = jest.spyOn(cycler, 'cleanup');
      cycler.destroy();
      expect(cleanupSpy).toHaveBeenCalled();
    });
  });

  describe('Integration test', () => {
    test('complete hover cycle works correctly', () => {
      cycler.init(mockVideoPlayer);

      const card = document.querySelector('.highlight-card');
      const images = document.querySelectorAll('.preview-image');

      // Initially first image is active
      expect(images[0]).toHaveClass('active');

      // Hover over card
      card.dispatchEvent(new Event('mouseenter'));

      // Advance time
      jest.advanceTimersByTime(800);
      expect(images[1]).toHaveClass('active');

      jest.advanceTimersByTime(800);
      expect(images[2]).toHaveClass('active');

      // Mouse leaves
      card.dispatchEvent(new Event('mouseleave'));

      // Should reset to first image
      expect(images[0]).toHaveClass('active');
      expect(images[1]).not.toHaveClass('active');
      expect(images[2]).not.toHaveClass('active');
    });
  });

  describe('Window export', () => {
    test('exports PreviewCycler to window', () => {
      expect(window.PreviewCycler).toBeDefined();
      expect(window.PreviewCycler).toBe(PreviewCycler);
    });
  });
});
