/**
 * Tests for VideoPlayer Module
 */

import { VideoPlayer } from '../superb_ock/static/superb_ock/js/modules/video-player.js';

describe('VideoPlayer', () => {
  let player;
  let videoElement;
  let modalElement;
  let modalTitleElement;

  beforeEach(() => {
    // Set up DOM
    document.body.innerHTML = `
      <video id="testVideo"></video>
      <div id="testModal" class="modal">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 id="testModalTitle" class="modal-title"></h5>
            </div>
          </div>
        </div>
      </div>
    `;

    videoElement = document.getElementById('testVideo');
    modalElement = document.getElementById('testModal');
    modalTitleElement = document.getElementById('testModalTitle');

    player = new VideoPlayer('testVideo', 'testModal', 'testModalTitle');
  });

  afterEach(() => {
    if (player) {
      player.destroy();
    }
    document.body.innerHTML = '';
  });

  describe('Initialization', () => {
    test('initializes with correct elements', () => {
      expect(player.video).toBe(videoElement);
      expect(player.modalElement).toBe(modalElement);
      expect(player.modalTitle).toBe(modalTitleElement);
    });

    test('creates Bootstrap modal instance', () => {
      expect(player.modal).toBeDefined();
      expect(player.modal).not.toBeNull();
    });

    test('initializes empty preloaded videos set', () => {
      expect(player.preloadedVideos).toBeInstanceOf(Set);
      expect(player.preloadedVideos.size).toBe(0);
    });

    test('sets up event listeners', () => {
      // Modal should have hidden.bs.modal listener
      const spy = jest.spyOn(player, 'cleanup');
      modalElement.dispatchEvent(new Event('hidden.bs.modal'));
      expect(spy).toHaveBeenCalled();
    });

    test('handles missing video element gracefully', () => {
      document.body.innerHTML = '<div id="testModal"></div>';
      const player2 = new VideoPlayer('nonexistent', 'testModal', 'testModalTitle');
      expect(player2.video).toBeNull();
    });

    test('handles missing modal element gracefully', () => {
      document.body.innerHTML = '<video id="testVideo"></video>';
      const player2 = new VideoPlayer('testVideo', 'nonexistent', 'testModalTitle');
      expect(player2.modal).toBeNull();
    });
  });

  describe('play() method', () => {
    test('sets video source', () => {
      player.play('https://example.com/video.mp4', 'Test Video');
      expect(videoElement.src).toBe('https://example.com/video.mp4');
    });

    test('updates modal title', () => {
      player.play('https://example.com/video.mp4', 'Test Video');
      expect(modalTitleElement.textContent).toBe('Test Video');
    });

    test('includes context in title', () => {
      player.play('https://example.com/video.mp4', 'Highlight', 'Hole 7');
      expect(modalTitleElement.textContent).toBe('Highlight - Hole 7');
    });

    test('shows modal', () => {
      player.play('https://example.com/video.mp4', 'Test Video');
      expect(player.modal._isShown).toBe(true);
    });

    test('sets loading state', () => {
      player.play('https://example.com/video.mp4', 'Test Video');
      expect(videoElement.style.opacity).toBe('0.7');
    });

    test('handles missing video element', () => {
      player.video = null;
      expect(() => {
        player.play('https://example.com/video.mp4', 'Test');
      }).not.toThrow();
    });

    test('handles missing modal', () => {
      player.modal = null;
      expect(() => {
        player.play('https://example.com/video.mp4', 'Test');
      }).not.toThrow();
    });

    test('uses default title if not provided', () => {
      player.play('https://example.com/video.mp4');
      expect(modalTitleElement.textContent).toBe('Golf Highlight');
    });
  });

  describe('handleVideoLoading() method', () => {
    test('removes loading state on canplay', (done) => {
      player.play('https://example.com/video.mp4', 'Test');

      videoElement.dispatchEvent(new Event('canplay'));

      setTimeout(() => {
        expect(videoElement.style.opacity).toBe('1');
        done();
      }, 10);
    });

    test('handles video errors', (done) => {
      player.play('https://example.com/video.mp4', 'Test');

      videoElement.dispatchEvent(new Event('error'));

      setTimeout(() => {
        expect(videoElement.style.opacity).toBe('1');
        done();
      }, 10);
    });
  });

  describe('preload() method', () => {
    test('creates link preload element', () => {
      player.preload('https://example.com/video.mp4');

      const preloadLink = document.querySelector('link[rel="preload"]');
      expect(preloadLink).toBeInTheDocument();
      expect(preloadLink.href).toBe('https://example.com/video.mp4');
      expect(preloadLink.as).toBe('video');
    });

    test('marks video as preloaded', () => {
      player.preload('https://example.com/video.mp4');
      expect(player.preloadedVideos.has('https://example.com/video.mp4')).toBe(true);
    });

    test('does not preload same video twice', () => {
      const initialPreloadCount = player.preloadedVideos.size;

      player.preload('https://example.com/video.mp4');
      expect(player.preloadedVideos.size).toBe(initialPreloadCount + 1);

      player.preload('https://example.com/video.mp4');
      expect(player.preloadedVideos.size).toBe(initialPreloadCount + 1); // Should still be same
    });
  });

  describe('cleanup() method', () => {
    test('pauses video', () => {
      const pauseSpy = jest.spyOn(videoElement, 'pause');
      player.cleanup();
      expect(pauseSpy).toHaveBeenCalled();
    });

    test('resets video time', () => {
      videoElement.currentTime = 10;
      player.cleanup();
      expect(videoElement.currentTime).toBe(0);
    });

    test('clears video source', () => {
      const initialSrc = videoElement.src;
      videoElement.src = 'https://example.com/video.mp4';
      player.cleanup();
      // jsdom sets empty src to current page URL, so just check it changed
      expect(videoElement.src).not.toBe('https://example.com/video.mp4');
    });

    test('handles missing video element', () => {
      player.video = null;
      expect(() => {
        player.cleanup();
      }).not.toThrow();
    });
  });

  describe('destroy() method', () => {
    test('calls cleanup', () => {
      const cleanupSpy = jest.spyOn(player, 'cleanup');
      player.destroy();
      expect(cleanupSpy).toHaveBeenCalled();
    });

    test('disposes modal', () => {
      const disposeSpy = jest.spyOn(player.modal, 'dispose');
      player.destroy();
      expect(disposeSpy).toHaveBeenCalled();
    });

    test('handles missing modal', () => {
      player.modal = null;
      expect(() => {
        player.destroy();
      }).not.toThrow();
    });
  });

  describe('Event listeners', () => {
    test('cleanup is called on modal hide', () => {
      const cleanupSpy = jest.spyOn(player, 'cleanup');
      modalElement.dispatchEvent(new Event('hidden.bs.modal'));
      expect(cleanupSpy).toHaveBeenCalled();
    });
  });

  describe('Window export', () => {
    test('exports VideoPlayer to window', () => {
      expect(window.VideoPlayer).toBeDefined();
      expect(window.VideoPlayer).toBe(VideoPlayer);
    });
  });
});
