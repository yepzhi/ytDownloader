import os
import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import subprocess
import tempfile

app = FastAPI()

# CORS - Allow GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: str
    type: str = "video"

class DownloadRequest(BaseModel):
    url: str
    format_id: str
    type: str = "video"

class AnalyzeRequest(BaseModel):
    url: str
    format_id: str

def get_ydl_opts():
    return {
        'quiet': True, 
        'no_warnings': True,
        'socket_timeout': 15,
    }

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "ytDownloader API is running"}

@app.post("/formats")
async def get_formats(req: URLRequest):
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(req.url, download=False)
            
            formats = []
            if 'formats' in info:
                for f in info['formats']:
                    if req.type == 'video' and f.get('vcodec') != 'none':
                        label = f"{f.get('resolution', 'Unknown')} ({f.get('ext')}) - {f.get('format_note', '')}"
                        formats.append({
                            'format_id': f['format_id'],
                            'label': label,
                            'ext': f['ext'],
                            'filesize': f.get('filesize', 0),
                            'quality': 'good',
                            'abr': 0
                        })
                    elif req.type == 'audio' and f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        abr = f.get('abr', 0) or 0
                        q_tag = 'fair'
                        if abr >= 128: q_tag = 'good'
                        if abr >= 160: q_tag = 'excellent'
                        label = f"{int(abr)}kbps ({f.get('ext')}) - {f.get('acodec', '')}"
                        formats.append({
                            'format_id': f['format_id'],
                            'label': label,
                            'ext': f['ext'],
                            'quality': q_tag,
                            'abr': abr
                        })
            
            # Sort by bitrate (highest first)
            formats.sort(key=lambda x: x.get('abr', 0), reverse=True)
            
            # Add "Best Audio" option at the top for audio
            if req.type == 'audio' and formats:
                formats.insert(0, {
                    'format_id': 'bestaudio',
                    'label': '⭐ BEST AUDIO (Auto-Select Highest)',
                    'ext': 'm4a',
                    'quality': 'excellent',
                    'abr': 999
                })
            
            return {"formats": formats, "title": info.get('title', 'Video')}
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/download")
async def download_video(req: DownloadRequest):
    cmd = [
        "yt-dlp", 
        "-f", req.format_id,
        "-o", "-",
        req.url
    ]
    
    try:
        def iterfile():
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                while True:
                    chunk = proc.stdout.read(65536)
                    if not chunk:
                        break
                    yield chunk
                    
        return StreamingResponse(iterfile(), media_type="application/octet-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-audio")
async def analyze_audio(req: AnalyzeRequest):
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(req.url, download=False)
            tgt = next((f for f in info['formats'] if f['format_id'] == req.format_id), None)
            
            if not tgt:
                return {"error": "Format not found"}
                
            abr = tgt.get('abr', 0) or 0
            asr = tgt.get('asr', 0) or 0
            acodec = tgt.get('acodec', 'unknown')
            
            quality = "fair"
            if abr >= 128: quality = "good"
            if abr >= 160: quality = "excellent"
            
            return {
                "analysis": {
                    "quality": quality,
                    "bitrate": f"{int(abr)} kbps",
                    "sample_rate": f"{int(asr)} Hz",
                    "codec": acodec,
                }
            }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
