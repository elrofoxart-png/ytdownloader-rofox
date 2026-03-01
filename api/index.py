# Vercel Serverless Function - Video Info Only
from flask import Flask, render_template, request, jsonify
import urllib.request
import urllib.error
import json
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

# Multiple Piped instances for fallback
PIPED_INSTANCES = [
    "https://api.piped.projectkavin.com",
    "https://pipedapi.moomoo.me",
    "https://api.piped.privacydev.net",
    "https://pipedapi.adminforge.de",
    "https://pipedapi.leptons.xyz",
    "https://api.piped.lunar.icu"
]

def extract_video_id(url):
    """Extract YouTube video ID"""
    if not url:
        return None
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    if hostname == "youtu.be":
        return parsed.path[1:] if len(parsed.path) > 1 else None
    if hostname in ("www.youtube.com", "youtube.com", "m.youtube.com", "www.youtube-nocookie.com"):
        if parsed.path == "/watch":
            params = parse_qs(parsed.query)
            v = params.get("v", [None])[0]
            return v
        if parsed.path.startswith(("/embed/", "/v/", "/shorts/")):
            parts = parsed.path.split("/")
            return parts[2] if len(parts) > 2 else None
    return None

def fetch_piped(video_id, timeout=15):
    """Try multiple Piped instances"""
    errors = []
    
    for instance in PIPED_INSTANCES:
        try:
            url = f"{instance}/streams/{video_id}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.0",
                    "Accept": "application/json"
                }
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    data["_instance"] = instance  # Track which instance worked
                    return data
                    
        except urllib.error.HTTPError as e:
            errors.append(f"{instance}: HTTP {e.code}")
            if e.code == 500:  # Video might be restricted, try next
                continue
        except urllib.error.URLError as e:
            errors.append(f"{instance}: {str(e.reason)}")
        except Exception as e:
            errors.append(f"{instance}: {str(e)}")
    
    return {"_errors": errors}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/info", methods=["POST"])
def get_info():
    try:
        url = request.json.get("url", "") if request.is_json else None
        if not url:
            return jsonify({"error": "URL required"}), 400
        
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL. Must be youtube.com/watch?v=... or youtu.be/ID"}), 400
        
        # Fetch from Piped
        data = fetch_piped(video_id)
        
        if "_errors" in data:
            error_msg = "; ".join(data["_errors"][:3])
            return jsonify({
                "error": "All Piped instances failed",
                "details": error_msg,
                "suggestion": "Video may be age-restricted, private, or unavailable in your region"
            }), 500
        
        # Format duration
        duration = data.get("duration", 0)
        mins = duration // 60
        secs = duration % 60
        
        # Build formats list
        formats = []
        
        # Video streams (no audio in these on Piped)
        for stream in data.get("videoStreams", [])[:6]:
            if stream.get("url"):
                formats.append({
                    "format_id": "video",
                    "quality": stream.get("qualityLabel", "unknown"),
                    "ext": "mp4",
                    "type": "video",
                    "url": stream.get("url"),
                    "codec": stream.get("codec", "")
                })
        
        # Audio streams
        for stream in data.get("audioStreams", [])[:4]:
            if stream.get("url"):
                formats.append({
                    "format_id": "audio",
                    "quality": stream.get("quality", "unknown"),
                    "ext": "m4a" if "m4a" in stream.get("format", "") else stream.get("format", "mp3").split("/")[-1],
                    "type": "audio",
                    "url": stream.get("url"),
                    "bitrate": stream.get("bitrate", 0)
                })
        
        # HLS stream if available (best quality)
        hls = data.get("hls", "")
        
        return jsonify({
            "id": video_id,
            "title": data.get("title", "Unknown"),
            "thumbnail": data.get("thumbnailUrl") or data.get("thumbnail", ""),
            "duration": f"{mins}:{secs:02d}",
            "uploader": data.get("uploader", "Unknown"),
            "uploader_url": data.get("uploaderUrl", ""),
            "view_count": data.get("views", 0),
            "uploaded": data.get("uploaded", ""),
            "hls_stream": hls,
            "formats": formats,
            "_source": data.get("_instance", "unknown")
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "trace": traceback.format_exc()
        }), 500

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "platform": "vercel",
        "piped_instances": len(PIPED_INSTANCES)
    })

# For local testing
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
