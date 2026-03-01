# Vercel Serverless Function - Video Info Only
# yt-dlp downloads NOT possible on Vercel (no subprocess, no persistent storage)

from flask import Flask, render_template, request, jsonify
import requests
import re
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

def extract_video_id(url):
    """Extract YouTube video ID"""
    parsed = urlparse(url)
    if parsed.hostname == 'youtu.be':
        return parsed.path[1:]
    if parsed.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
        if parsed.path.startswith('/embed/'):
            return parsed.path.split('/')[2]
        if parsed.path.startswith('/v/'):
            return parsed.path.split('/')[2]
    return None

def get_piped_info(video_id):
    """Get video info from Piped API (public YouTube proxy)"""
    instances = [
        "https://api.piped.projectkavin.com",
        "https://pipedapi.moomoo.me",
        "https://api.piped.privacydev.net",
        "https://pipedapi.adminforge.de"
    ]
    
    for instance in instances:
        try:
            url = f"{instance}/streams/{video_id}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
        except:
            continue
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
    
    data = get_piped_info(video_id)
    if not data:
        return jsonify({'error': 'Could not fetch video info'}), 500
    
    # Format duration
    duration = data.get('duration', 0)
    mins = duration // 60
    secs = duration % 60
    
    # Build format list from Piped
    formats = []
    
    # Video streams
    for stream in data.get('videoStreams', [])[:5]:
        formats.append({
            'format_id': stream.get('url', '')[-20:-10] or 'video',
            'quality': f"{stream.get('quality', 'unknown')}p",
            'ext': stream.get('format', 'mp4').split('/')[-1],
            'has_video': True,
            'has_audio': stream.get('quality') == 'audio',  # Piped separates
            'url': stream.get('url')
        })
    
    # Audio streams
    for stream in data.get('audioStreams', [])[:3]:
        formats.append({
            'format_id': stream.get('url', '')[-20:-10] or 'audio',
            'quality': f"Audio {stream.get('quality', 'unknown')}bps",
            'ext': stream.get('format', 'mp4').split('/')[-1],
            'has_video': False,
            'has_audio': True,
            'url': stream.get('url')
        })
    
    return jsonify({
        'id': video_id,
        'title': data.get('title', 'Unknown'),
        'thumbnail': data.get('thumbnailUrl') or data.get('thumbnail', ''),
        'duration': f"{mins}:{secs:02d}",
        'uploader': data.get('uploader', 'Unknown'),
        'uploader_url': data.get('uploaderUrl', ''),
        'view_count': data.get('views', 0),
        'formats': formats
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'platform': 'vercel'})
