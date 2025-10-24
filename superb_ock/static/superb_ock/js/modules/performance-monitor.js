/**
 * Performance Monitor Module
 * Simple performance timing metrics without external dependencies
 * Only displays in development mode (DEBUG=True)
 */

class PerformanceMonitor {
  constructor(options = {}) {
    this.enabled = options.enabled !== false;
    this.showPanel = options.showPanel !== false;
    this.metrics = {};
    this.panel = null;

    if (this.enabled && 'performance' in window) {
      this.init();
    }
  }

  /**
   * Initialize performance monitoring
   */
  init() {
    // Wait for page to fully load
    if (document.readyState === 'complete') {
      this.collectMetrics();
    } else {
      window.addEventListener('load', () => {
        this.collectMetrics();
      });
    }
  }

  /**
   * Collect performance metrics
   */
  collectMetrics() {
    const perfData = performance.getEntriesByType('navigation')[0];
    const paintData = performance.getEntriesByType('paint');

    if (!perfData) return;

    // Timing metrics
    this.metrics = {
      // Page load timing
      dns: this.round(perfData.domainLookupEnd - perfData.domainLookupStart),
      tcp: this.round(perfData.connectEnd - perfData.connectStart),
      ttfb: this.round(perfData.responseStart - perfData.requestStart),
      download: this.round(perfData.responseEnd - perfData.responseStart),
      domInteractive: this.round(perfData.domInteractive),
      domComplete: this.round(perfData.domComplete),
      loadComplete: this.round(perfData.loadEventEnd),

      // Paint timing
      firstPaint: this.getPaintTiming(paintData, 'first-paint'),
      firstContentfulPaint: this.getPaintTiming(paintData, 'first-contentful-paint'),

      // Resource counts
      resources: performance.getEntriesByType('resource').length,

      // Memory (if available)
      memory: this.getMemoryInfo()
    };

    // Log to console in development
    this.logMetrics();

    // Show panel if enabled
    if (this.showPanel) {
      this.createPanel();
    }
  }

  /**
   * Get paint timing
   * @param {Array} paintData - Paint timing data
   * @param {string} name - Paint name
   * @returns {number} Paint time in ms
   */
  getPaintTiming(paintData, name) {
    const entry = paintData.find(p => p.name === name);
    return entry ? this.round(entry.startTime) : null;
  }

  /**
   * Get memory info (Chrome only)
   * @returns {Object|null} Memory info
   */
  getMemoryInfo() {
    if (performance.memory) {
      return {
        used: this.formatBytes(performance.memory.usedJSHeapSize),
        total: this.formatBytes(performance.memory.totalJSHeapSize),
        limit: this.formatBytes(performance.memory.jsHeapSizeLimit)
      };
    }
    return null;
  }

  /**
   * Round number to 2 decimal places
   * @param {number} num - Number to round
   * @returns {number} Rounded number
   */
  round(num) {
    return Math.round(num * 100) / 100;
  }

  /**
   * Format bytes to human readable
   * @param {number} bytes - Bytes
   * @returns {string} Formatted string
   */
  formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return this.round(bytes / Math.pow(k, i)) + ' ' + sizes[i];
  }

  /**
   * Log metrics to console
   */
  logMetrics() {
    console.group('⚡ Performance Metrics');
    console.log('DNS Lookup:', this.metrics.dns + 'ms');
    console.log('TCP Connection:', this.metrics.tcp + 'ms');
    console.log('Time to First Byte:', this.metrics.ttfb + 'ms');
    console.log('Download Time:', this.metrics.download + 'ms');
    console.log('DOM Interactive:', this.metrics.domInteractive + 'ms');
    console.log('DOM Complete:', this.metrics.domComplete + 'ms');
    console.log('Load Complete:', this.metrics.loadComplete + 'ms');

    if (this.metrics.firstPaint) {
      console.log('First Paint:', this.metrics.firstPaint + 'ms');
    }
    if (this.metrics.firstContentfulPaint) {
      console.log('First Contentful Paint:', this.metrics.firstContentfulPaint + 'ms');
    }

    console.log('Resources Loaded:', this.metrics.resources);

    if (this.metrics.memory) {
      console.log('Memory Used:', this.metrics.memory.used);
      console.log('Memory Total:', this.metrics.memory.total);
    }
    console.groupEnd();
  }

  /**
   * Create performance panel overlay
   */
  createPanel() {
    // Don't create if already exists
    if (document.getElementById('perf-monitor-panel')) {
      return;
    }

    this.panel = document.createElement('div');
    this.panel.id = 'perf-monitor-panel';
    this.panel.className = 'perf-panel';
    this.panel.innerHTML = this.getPanelHTML();

    document.body.appendChild(this.panel);
    this.injectStyles();

    // Add toggle button
    const toggleBtn = this.panel.querySelector('.perf-toggle');
    toggleBtn.addEventListener('click', () => {
      this.panel.classList.toggle('collapsed');
    });

    // Add close button
    const closeBtn = this.panel.querySelector('.perf-close');
    closeBtn.addEventListener('click', () => {
      this.panel.remove();
    });
  }

  /**
   * Generate panel HTML
   * @returns {string} HTML string
   */
  getPanelHTML() {
    const getColor = (value, warning, danger) => {
      if (value > danger) return 'danger';
      if (value > warning) return 'warning';
      return 'success';
    };

    return `
      <div class="perf-header">
        <span class="perf-title">⚡ Performance</span>
        <div class="perf-controls">
          <button class="perf-toggle" title="Toggle panel" aria-label="Toggle performance panel">
            <i class="fas fa-chevron-down"></i>
          </button>
          <button class="perf-close" title="Close panel" aria-label="Close performance panel">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
      <div class="perf-body">
        <div class="perf-section">
          <h6>Page Load</h6>
          <div class="perf-metric">
            <span>Time to First Byte</span>
            <span class="perf-value perf-${getColor(this.metrics.ttfb, 200, 500)}">
              ${this.metrics.ttfb}ms
            </span>
          </div>
          <div class="perf-metric">
            <span>First Contentful Paint</span>
            <span class="perf-value perf-${getColor(this.metrics.firstContentfulPaint, 1500, 2500)}">
              ${this.metrics.firstContentfulPaint || 'N/A'}${this.metrics.firstContentfulPaint ? 'ms' : ''}
            </span>
          </div>
          <div class="perf-metric">
            <span>DOM Complete</span>
            <span class="perf-value perf-${getColor(this.metrics.domComplete, 2000, 4000)}">
              ${this.metrics.domComplete}ms
            </span>
          </div>
          <div class="perf-metric">
            <span>Load Complete</span>
            <span class="perf-value perf-${getColor(this.metrics.loadComplete, 3000, 5000)}">
              ${this.metrics.loadComplete}ms
            </span>
          </div>
        </div>

        <div class="perf-section">
          <h6>Network</h6>
          <div class="perf-metric">
            <span>DNS Lookup</span>
            <span class="perf-value">${this.metrics.dns}ms</span>
          </div>
          <div class="perf-metric">
            <span>TCP Connection</span>
            <span class="perf-value">${this.metrics.tcp}ms</span>
          </div>
          <div class="perf-metric">
            <span>Download Time</span>
            <span class="perf-value">${this.metrics.download}ms</span>
          </div>
          <div class="perf-metric">
            <span>Resources Loaded</span>
            <span class="perf-value">${this.metrics.resources}</span>
          </div>
        </div>

        ${this.metrics.memory ? `
          <div class="perf-section">
            <h6>Memory (Chrome)</h6>
            <div class="perf-metric">
              <span>Used</span>
              <span class="perf-value">${this.metrics.memory.used}</span>
            </div>
            <div class="perf-metric">
              <span>Total</span>
              <span class="perf-value">${this.metrics.memory.total}</span>
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * Inject panel styles
   */
  injectStyles() {
    if (document.getElementById('perf-monitor-styles')) {
      return;
    }

    const style = document.createElement('style');
    style.id = 'perf-monitor-styles';
    style.textContent = `
      .perf-panel {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 320px;
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13px;
        z-index: 9998;
        transition: transform 0.3s ease;
      }

      .perf-panel.collapsed .perf-body {
        display: none;
      }

      .perf-panel.collapsed .perf-toggle i {
        transform: rotate(-90deg);
      }

      .perf-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid #dee2e6;
        background: #f8f9fa;
        border-radius: 8px 8px 0 0;
      }

      .perf-title {
        font-weight: 600;
        font-size: 14px;
      }

      .perf-controls {
        display: flex;
        gap: 8px;
      }

      .perf-toggle,
      .perf-close {
        background: none;
        border: none;
        cursor: pointer;
        padding: 4px 8px;
        color: #6c757d;
        transition: color 0.2s;
      }

      .perf-toggle:hover,
      .perf-close:hover {
        color: #212529;
      }

      .perf-toggle i {
        transition: transform 0.3s;
      }

      .perf-body {
        padding: 12px 16px;
        max-height: 400px;
        overflow-y: auto;
      }

      .perf-section {
        margin-bottom: 16px;
      }

      .perf-section:last-child {
        margin-bottom: 0;
      }

      .perf-section h6 {
        font-size: 11px;
        text-transform: uppercase;
        font-weight: 600;
        color: #6c757d;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
      }

      .perf-metric {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid #f1f3f5;
      }

      .perf-metric:last-child {
        border-bottom: none;
      }

      .perf-value {
        font-weight: 600;
        font-family: 'Monaco', 'Menlo', monospace;
      }

      .perf-success {
        color: #28a745;
      }

      .perf-warning {
        color: #ffc107;
      }

      .perf-danger {
        color: #dc3545;
      }

      /* Dark mode */
      [data-bs-theme="dark"] .perf-panel {
        background: #212529;
        border-color: #495057;
      }

      [data-bs-theme="dark"] .perf-header {
        background: #343a40;
        border-color: #495057;
      }

      [data-bs-theme="dark"] .perf-metric {
        border-color: #343a40;
      }

      /* Mobile */
      @media (max-width: 768px) {
        .perf-panel {
          width: calc(100% - 40px);
          bottom: 10px;
          right: 10px;
        }
      }
    `;

    document.head.appendChild(style);
  }

  /**
   * Get metrics object
   * @returns {Object} Metrics
   */
  getMetrics() {
    return this.metrics;
  }

  /**
   * Measure custom timing
   * @param {string} name - Name of measurement
   * @param {Function} fn - Function to measure
   * @returns {Promise} Result of function
   */
  async measure(name, fn) {
    const start = performance.now();
    const result = await fn();
    const end = performance.now();
    const duration = this.round(end - start);

    console.log(`⏱️ ${name}: ${duration}ms`);
    return result;
  }

  /**
   * Start a custom mark
   * @param {string} name - Mark name
   */
  mark(name) {
    performance.mark(name);
  }

  /**
   * Measure between two marks
   * @param {string} name - Measurement name
   * @param {string} startMark - Start mark name
   * @param {string} endMark - End mark name
   */
  measureBetween(name, startMark, endMark) {
    try {
      performance.measure(name, startMark, endMark);
      const measure = performance.getEntriesByName(name)[0];
      console.log(`⏱️ ${name}: ${this.round(measure.duration)}ms`);
    } catch (e) {
      console.error('Error measuring:', e);
    }
  }
}

// Export for module usage
export { PerformanceMonitor };

// Auto-initialize for browser usage (only in development)
if (typeof window !== 'undefined') {
  window.PerformanceMonitor = PerformanceMonitor;

  // Check if in development mode
  const isDevelopment = window.location.hostname === 'localhost' ||
                        window.location.hostname === '127.0.0.1' ||
                        document.body.hasAttribute('data-debug');

  if (isDevelopment) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        window.perfMonitor = new PerformanceMonitor();
      });
    } else {
      window.perfMonitor = new PerformanceMonitor();
    }
  }
}
