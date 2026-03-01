# YouTube Downloader - Vercel Edition

Get YouTube video info and direct stream links via Piped API.

## Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/import?repository-url=https://github.com/elrofoxart-png/ytdownloader-rofox)

## Features
- No server-side downloads
- Direct stream URLs
- Uses Piped instances (public YouTube proxy)
- Dark mode UI

## Local Dev
```bash
cd api
pip install flask requests
python index.py
```

## API Endpoints
- `POST /api/info` - Get video info
- `GET /api/health` - Health check
