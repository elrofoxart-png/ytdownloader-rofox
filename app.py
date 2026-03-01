#!/usr/bin/env python3
"""
YouTube Downloader Clone
Local web app for downloading YouTube videos/audio
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

# Configuration
DOWNLOAD_FOLDER = Path("downloads")
DOWNLOAD_FOLDER.mkdir(exist_ok=True)

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    parsed = urlparse(url)
    if parsed.hostname in ('youtu.be',):
        return parsed.path[1:]
    if parsed.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
        if parsed.path.startswith('/embed/'):
            return parsed.path.split('/')[2]
        if parsed.path.startswith('/v/'):
            return parsed.path.split('/')[2]
    return None

def get_video_info(url):
    """Get video info using yt-dlp"""
    try:
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--skip-download',
            '--no-warnings',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    url = request.json.get('url', '')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    info = get_video_info(url)
    if not info:
        return jsonify({'error': 'Could not fetch video info'}), 500
    
    return jsonify({
        'id': video_id,
        'title': info.get('title', 'Unknown'),
        'thumbnail': info.get('thumbnail', ''),
        'duration': info.get('duration', 0),
        'uploader': info.get('uploader', 'Unknown'),
        'formats': [
            {
                'format_id': f.get('format_id', ''),
                'quality': f.get('quality_label', f.get('format_note', 'unknown')),
                'ext': f.get('ext', 'mp4'),
                'has_video': f.get('vcodec') != 'none',
                'has_audio': f.get('acodec') != 'none'
            }
            for f in info.get('formats', [])[:10]  # Limit formats
        ]
    })

@app.route('/api/download', methods=['POST'])
def download():
    url = request.json.get('url', '')
    download_type = request.json.get('type', 'video')  # 'video' or 'audio'
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    try:
        output_path = DOWNLOAD_FOLDER / f"%(title)s_%(id)s.%(ext)s"
        
        if download_type == 'audio':
            # Download audio only
            cmd = [
                'yt-dlp',
                '-f', 'bestaudio/best',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '-o', str(output_path),
                '--no-warnings',
                url
            ]
        else:
            # Download video
            cmd = [
                'yt-dlp',
                '-f', 'best[ext=mp4]/best',
                '-o', str(output_path),
                '--no-warnings',
                url
            ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Find downloaded file
            for file in DOWNLOAD_FOLDER.iterdir():
                if video_id in file.name:
                    return jsonify({
                        'success': True,
                        'filename': file.name,
                        'path': str(file)
                    })
        
        return jsonify({'error': 'Download failed', 'details': result.stderr}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<path:filename>')
def serve_file(filename):
    file_path = DOWNLOAD_FOLDER / filename
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    print("🚀 YouTube Downloader Server")
    print(f"📁 Downloads folder: {DOWNLOAD_FOLDER.absolute()}")
    print("➡️  Open http://localhost:5000 in your browser")
    app.run(host='0.0.0.0', port=5000, debug=True)
