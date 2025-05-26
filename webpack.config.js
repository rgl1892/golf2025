const path = require('path');
const BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  context: __dirname,
  entry: {
    main: './assets/js/index.js',
    scorecard: './assets/js/components/Scorecard.js',
  },
  output: {
    path: path.resolve('./assets/webpack_bundles/'),
    filename: '[name]-[hash].js',
    publicPath: '/static/webpack_bundles/',
  },
  plugins: [
    new BundleTracker({filename: './webpack-stats.json'}),
  ],
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react'],
          },
        },
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  resolve: {
    extensions: ['.js', '.jsx'],
  },
};
