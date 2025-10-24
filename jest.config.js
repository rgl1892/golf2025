module.exports = {
  // Use jsdom environment for DOM testing
  testEnvironment: 'jsdom',

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // Test file patterns
  testMatch: [
    '**/tests/**/*.test.js',
    '**/__tests__/**/*.js'
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'superb_ock/static/superb_ock/js/modules/**/*.js',
    '!superb_ock/static/superb_ock/js/modules/**/*.test.js'
  ],

  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },

  // Transform files with Babel
  transform: {
    '^.+\\.js$': 'babel-jest'
  },

  // Module paths
  modulePaths: ['<rootDir>'],

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/venv/',
    '/.git/'
  ],

  // Verbose output
  verbose: true
};
