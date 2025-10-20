/**
 * Video Player Tests
 *
 * Tests for the VideoPlayer module
 */

import { VideoPlayer } from '../modules/video-player.js';

describe('VideoPlayer', () => {
  let videoPlayer;
  let mockVideoElement;
  let mockModalElement;
  let mockTitleElement;

  beforeEach(() => {
    // Setup DOM
    document.body.innerHTML = `
      <div id="videoModal" class="modal">
        <h5 id="videoModalTitle"></h5>
      </div>
      <video id="highlightVideo"></video>
    `;

    mockVideoElement = document.getElementById('highlightVideo');
    mockModalElement = document.getElementById('videoModal');
    mockTitleElement = document.getElementById('videoModalTitle');

    // Mock video methods
    mockVideoElement.load = jest.fn();
    mockVideoElement.play = jest.fn().mockResolvedValue(undefined);
    mockVideoElement.pause = jest.fn();

    videoPlayer = new VideoPlayer('highlightVideo', 'videoModal', 'videoModalTitle');
  });

  describe('Initialization', () => {
    test('finds and stores video element', () => {
      expect(videoPlayer.video).toBe(mockVideoElement);
    });

    test('creates Bootstrap modal instance', () => {
      expect(videoPlayer.modal).toBeDefined();
    });

    test('finds title element', () => {
      expect(videoPlayer.modalTitle).toBe(mockTitleElement);
    });

    test('initializes preloaded videos set', () => {
      expect(videoPlayer.preloadedVideos).toBeInstanceOf(Set);
      expect(videoPlayer.preloadedVideos.size).toBe(0);
    });
  });

  describe('Play video', () => {
    test('loads video source', () => {
      const videoUrl = '/media/highlights/video.mp4';
      videoPlayer.play(videoUrl, 'Test Title');

      expect(mockVideoElement.src).toContain(videoUrl);
    });

    test('sets video title', () => {
      videoPlayer.play('/media/video.mp4', 'Amazing Shot');

      expect(mockTitleElement.textContent).toBe('Amazing Shot');
    });

    test('calls video load method', () => {
      videoPlayer.play('/media/video.mp4', 'Test');

      expect(mockVideoElement.load).toHaveBeenCalled();
    });

    test('shows modal', () => {
      videoPlayer.play('/media/video.mp4', 'Test');

      expect(mockModalElement).toHaveClass('show');
    });

    test('adds context to title if provided', () => {
      videoPlayer.play('/media/video.mp4', 'Great Putt', 'Hole 9');

      expect(mockTitleElement.textContent).toContain('Great Putt');
      expect(mockTitleElement.textContent).toContain('Hole 9');
    });
  });

  describe('Preload video', () => {
    test('preloads video URL', () => {
      const videoUrl = '/media/video.mp4';
      videoPlayer.preload(videoUrl);

      expect(videoPlayer.preloadedVideos.has(videoUrl)).toBe(true);
    });

    test('does not preload same video twice', () => {
      const videoUrl = '/media/video.mp4';

      videoPlayer.preload(videoUrl);
      const initialSize = videoPlayer.preloadedVideos.size;

      videoPlayer.preload(videoUrl);
      const finalSize = videoPlayer.preloadedVideos.size;

      expect(finalSize).toBe(initialSize);
    });

    test('creates link preload element', () => {
      videoPlayer.preload('/media/video.mp4');

      const preloadElements = document.head.querySelectorAll('link[rel="preload"][as="video"]');
      expect(preloadElements.length).toBeGreaterThan(0);
      expect(preloadElements[0].href).toContain('/media/video.mp4');
    });
  });

  describe('Cleanup', () => {
    test('pauses video on cleanup', () => {
      videoPlayer.play('/media/video.mp4', 'Test');
      videoPlayer.cleanup();

      expect(mockVideoElement.pause).toHaveBeenCalled();
    });

    test('removes video source on cleanup', () => {
      videoPlayer.play('/media/video.mp4', 'Test');

      // Verify video was set
      expect(mockVideoElement.src).toContain('video.mp4');

      videoPlayer.cleanup();

      // In jsdom, setting src='' results in 'http://localhost/'
      expect(mockVideoElement.src).not.toContain('video.mp4');
    });

    test('resets video currentTime on cleanup', () => {
      mockVideoElement.currentTime = 10;
      videoPlayer.cleanup();

      expect(mockVideoElement.currentTime).toBe(0);
    });
  });

  describe('Modal event handling', () => {
    test('sets up modal hidden event listener', () => {
      const pauseSpy = jest.spyOn(mockVideoElement, 'pause');

      // Trigger modal hidden
      mockModalElement.dispatchEvent(new Event('hidden.bs.modal'));

      expect(pauseSpy).toHaveBeenCalled();
    });
  });

  describe('Error handling', () => {
    test('handles missing video element gracefully', () => {
      document.body.innerHTML = '';

      expect(() => {
        new VideoPlayer('nonexistent', 'videoModal', 'videoModalTitle');
      }).not.toThrow();
    });

    test('handles play promise rejection', async () => {
      mockVideoElement.play.mockRejectedValue(new Error('Play failed'));

      expect(() => {
        videoPlayer.play('/media/video.mp4', 'Test');
      }).not.toThrow();
    });
  });

  describe('Video loading states', () => {
    test('applies loading opacity class', () => {
      videoPlayer.play('/media/video.mp4', 'Test');

      expect(mockVideoElement.style.opacity).toBe('0.7');
    });

    test('removes loading opacity when video loads', () => {
      videoPlayer.play('/media/video.mp4', 'Test');

      // Simulate video loaded (canplay event)
      mockVideoElement.dispatchEvent(new Event('canplay'));

      expect(mockVideoElement.style.opacity).toBe('1');
    });
  });
});
