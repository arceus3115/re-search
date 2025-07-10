const path = require('path');

module.exports = {
  mode: 'development',
  entry: './src/index.ts',
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  resolve: {
    extensions: ['.ts', '.js', '.css'],
  },
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'public'),

  },
  devServer: {
    static: {
      directory: path.join(__dirname, 'public'),
    },
    compress: true,
    port: 9000,
    proxy: [
      {
        context: ['/api'],
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    ],
  },
};
