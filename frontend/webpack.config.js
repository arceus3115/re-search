const path = require('path');
const webpack = require('webpack');
const fs = require('fs');

const isProduction = process.env.NODE_ENV === 'production';
const publicPath = process.env.PUBLIC_PATH || '/';
const apiBaseUrl = process.env.API_BASE_URL || '/api/v1';

module.exports = {
  mode: isProduction ? 'production' : 'development',
  entry: './src/index.ts',
  devtool: isProduction ? 'source-map' : 'eval-source-map',
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
    path: path.resolve(__dirname, 'dist'),
    publicPath,
    clean: true,
  },
  plugins: [
    new webpack.DefinePlugin({
      'process.env.API_BASE_URL': JSON.stringify(apiBaseUrl),
    }),
    {
      apply: (compiler) => {
        compiler.hooks.afterEmit.tap('CopyIndexHtml', () => {
          const indexPath = path.resolve(__dirname, 'public/index.html');
          const distPath = path.resolve(__dirname, 'dist/index.html');
          let html = fs.readFileSync(indexPath, 'utf8');
          html = html.replace('./bundle.js', `${publicPath}bundle.js`.replace(/\/+/g, '/'));
          fs.writeFileSync(distPath, html);
        });
      },
    },
  ],
  devServer: {
    static: {
      directory: path.join(__dirname, 'public'),
    },
    compress: true,
    port: 9000,
    proxy: [
      {
        context: ['/api'],
        target: process.env.BACKEND_PROXY_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    ],
  },
};
