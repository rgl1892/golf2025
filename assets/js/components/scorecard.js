import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ScoreInput = ({ score, onScoreChange, hole }) => {
  const [localScore, setLocalScore] = useState(score.shots_taken || hole.par);
  
  const calculateStableford = (shots, par, handicapStrokes) => {
    const extraShots = Math.floor(handicapStrokes / 18);
    const siShots = hole.stroke_index <= handicapStrokes ? 1 : 0;
    const strokesToPar = shots - par - extraShots - siShots;
    
    const stablefordMap = {
      '-4': 6, '-3': 5, '-2': 4, '-1': 3, '0': 2, '1': 1
    };
    
    return strokesToPar <= -4 ? 6 : (stablefordMap[strokesToPar] || 0);
  };

  const handleScoreChange = (newScore) => {
    if (newScore >= 0) {
      setLocalScore(newScore);
      const stableford = calculateStableford(newScore, hole.par, score.handicap_index);
      onScoreChange(score.id, {
        shots_taken: newScore,
        stableford: stableford
      });
    }
  };

  return (
    <div className="player-card">
      <h5>{score.player_name}</h5>
      <div className="score-entry">
        <button 
          className="btn btn-danger"
          onClick={() => handleScoreChange(localScore - 1)}
        >
          −
        </button>
        <input 
          type="number" 
          className="form-control score-input"
          value={localScore}
          onChange={(e) => handleScoreChange(parseInt(e.target.value) || 0)}
        />
        <button 
          className="btn btn-success"
          onClick={() => handleScoreChange(localScore + 1)}
        >
          +
        </button>
      </div>
      <div className="stable_out">
        Stableford: {score.stableford || 0}
      </div>
    </div>
  );
};

const HoleCard = ({ hole, scores, onScoresUpdate, isActive }) => {
  const [pendingChanges, setPendingChanges] = useState({});

  const handleScoreChange = (scoreId, newScoreData) => {
    setPendingChanges(prev => ({
      ...prev,
      [scoreId]: newScoreData
    }));
  };

  const submitChanges = async () => {
    if (Object.keys(pendingChanges).length === 0) return;

    try {
      const updates = Object.entries(pendingChanges).map(([scoreId, data]) => ({
        id: parseInt(scoreId),
        ...data
      }));

      await axios.patch('/api/scores/bulk_update/', { updates });
      onScoresUpdate();
      setPendingChanges({});
    } catch (error) {
      console.error('Failed to update scores:', error);
    }
  };

  // Auto-submit when switching holes
  useEffect(() => {
    if (!isActive && Object.keys(pendingChanges).length > 0) {
      submitChanges();
    }
  }, [isActive]);

  const holeScores = scores.filter(s => s.hole_number === hole.hole_number);

  return (
    <div className={`carousel-item ${isActive ? 'active' : ''}`}>
      <h3 className="text-center">Hole {hole.hole_number}</h3>
      <p className="text-center text-muted">
        Par: {hole.par} | Stroke Index: {hole.stroke_index}
      </p>
      
      {holeScores.map(score => (
        <ScoreInput
          key={score.id}
          score={{
            ...score,
            ...pendingChanges[score.id] // Apply pending changes
          }}
          hole={hole}
          onScoreChange={handleScoreChange}
        />
      ))}
      
      {Object.keys(pendingChanges).length > 0 && (
        <button 
          className="btn btn-primary mt-2"
          onClick={submitChanges}
        >
          Save Changes ({Object.keys(pendingChanges).length})
        </button>
      )}
    </div>
  );
};

const Scorecard = ({ roundId }) => {
  const [scores, setScores] = useState([]);
  const [holes, setHoles] = useState([]);
  const [currentHole, setCurrentHole] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRoundData();
  }, [roundId]);

  const fetchRoundData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/round/${roundId}/scores/`);
      const scoresData = response.data;
      
      setScores(scoresData);
      
      // Extract unique holes and sort them
      const uniqueHoles = [...new Set(scoresData.map(s => s.hole_number))]
        .sort((a, b) => a - b)
        .map(holeNum => {
          const scoreWithHole = scoresData.find(s => s.hole_number === holeNum);
          return {
            hole_number: holeNum,
            par: scoreWithHole.hole_par,
            stroke_index: scoreWithHole.hole?.stroke_index || 1
          };
        });
      
      setHoles(uniqueHoles);
    } catch (error) {
      console.error('Failed to fetch round data:', error);
    } finally {
      setLoading(false);
    }
  };

  const nextHole = () => {
    if (currentHole < holes.length - 1) {
      setCurrentHole(currentHole + 1);
    }
  };

  const prevHole = () => {
    if (currentHole > 0) {
      setCurrentHole(currentHole - 1);
    }
  };

  // Touch handling for mobile
  const [touchStart, setTouchStart] = useState(0);
  const [touchEnd, setTouchEnd] = useState(0);

  const handleTouchStart = (e) => {
    setTouchStart(e.targetTouches[0].clientX);
  };

  const handleTouchEnd = (e) => {
    setTouchEnd(e.changedTouches[0].clientX);
    handleSwipe();
  };

  const handleSwipe = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > 50;
    const isRightSwipe = distance < -50;

    if (isLeftSwipe) nextHole();
    if (isRightSwipe) prevHole();
  };

  if (loading) {
    return (
      <div className="text-center">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <button 
          className="btn btn-outline-primary"
          onClick={prevHole}
          disabled={currentHole === 0}
        >
          ← Previous
        </button>
        
        <div className="text-center">
          <h4>Hole {currentHole + 1} of {holes.length}</h4>
          <div className="progress" style={{height: '4px'}}>
            <div 
              className="progress-bar" 
              style={{width: `${((currentHole + 1) / holes.length) * 100}%`}}
            />
          </div>
        </div>
        
        <button 
          className="btn btn-outline-primary"
          onClick={nextHole}
          disabled={currentHole === holes.length - 1}
        >
          Next →
        </button>
      </div>

      <div 
        className="scorecard-container"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {holes.map((hole, index) => (
          <HoleCard
            key={hole.hole_number}
            hole={hole}
            scores={scores}
            onScoresUpdate={fetchRoundData}
            isActive={index === currentHole}
          />
        ))}
      </div>

      {/* Hole navigation dots */}
      <div className="text-center mt-3">
        {holes.map((_, index) => (
          <button
            key={index}
            className={`btn btn-sm mx-1 ${index === currentHole ? 'btn-primary' : 'btn-outline-secondary'}`}
            onClick={() => setCurrentHole(index)}
            style={{width: '30px', height: '30px', borderRadius: '50%'}}
          >
            {index + 1}
          </button>
        ))}
      </div>
    </div>
  );
};

export default Scorecard;

// assets/js/index.js - Main React entry point
import React from 'react';
import { createRoot } from 'react-dom/client';
import Scorecard from './components/Scorecard';

// Mount React components based on page
document.addEventListener('DOMContentLoaded', () => {
  // Mount Scorecard component
  const scorecardContainer = document.getElementById('react-scorecard');
  if (scorecardContainer) {
    const roundId = scorecardContainer.dataset.roundId;
    const root = createRoot(scorecardContainer);
    root.render(<Scorecard roundId={roundId} />);
  }
});