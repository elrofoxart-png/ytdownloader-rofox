# YouTube Downloader 

Clone de ytb.pco2.fr en Flask avec Docker.

## 🚀 Quick Start (Docker)

```bash
# 1. Clone
git clone https://github.com/elrofoxart-png/ytdownloader-rofox.git
cd ytdownloader-rofox

# 2. Lance avec Docker Compose
docker-compose up --build

# 3. Accède à l'app
open http://localhost:5000
```

## 📋 Features

- 📹 Téléchargement MP4 (vidéo)
- 🎵 Téléchargement MP3 (audio)  
- 🌙 Interface Dark Mode
- 🐳 100% Dockerisé

## 🏗️ Build manuel

```bash
# Sans Docker Compose
docker build -t ytdownloader .
docker run -p 5000:5000 -v $(pwd)/downloads:/downloads ytdownloader
```

## ⚠️ Notes

- Vercel = limité (Piped API souvent bloqué)
- **Docker = 100% fonctionnel avec vrai yt-dlp**
- Les downloads vont dans `./downloads/`

## 🔧 Tech Stack

- Flask + Python 3.11
- yt-dlp (téléchargement)
- FFmpeg (conversion audio)
- Docker + Compose
