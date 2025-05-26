import React from 'react';
import { createRoot } from 'react-dom/client';
import Scorecard from './components/Scorecard';
import './api-config'; // CSRF setup

// Auto-mount React components based on DOM elements
document.addEventListener('DOMContentLoaded', () => {
  // Mount Scorecard component
  const scorecardElement = document.getElementById('react-scorecard');
  if (scorecardElement) {
    const roundId = scorecardElement.dataset.roundId;
    const root = createRoot(scorecardElement);
    root.render(<Scorecard roundId={roundId} />);
  }
  
  // Mount other components as needed
  const heatmapElement = document.getElementById('react-heatmap');
  if (heatmapElement) {
    // Import and mount heatmap component
    import('./components/Heatmap').then(({ default: Heatmap }) => {
      const root = createRoot(heatmapElement);
      root.render(<Heatmap />);
    });
  }
});
