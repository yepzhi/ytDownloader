import os
import uvicorn
import yt_dlp
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
import json
import socket

app = FastAPI()

# Startup Check
@app.on_event("startup")
async def startup_event():
    print("--- STARTUP DNS CHECK ---")
    try:
        ip = socket.gethostbyname("www.youtube.com")
        print(f"DNS OK: www.youtube.com -> {ip}")
    except Exception as e:
        print(f"DNS FAIL: {e}")
    print("-------------------------")

# CORS
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

# Shared yt-dlp options
def get_ydl_opts():
    return {
        'quiet': True, 
        'no_warnings': True,
        'force_ipv4': True, 
        'socket_timeout': 15,
    }

@app.get("/")
async def read_root():
    return FileResponse('index.html')

@app.post("/formats")
async def get_formats(req: URLRequest):
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(req.url, download=False)
            
            formats = []
            if 'formats' in info:
                # Filter useful formats
                for f in info['formats']:
                    # Video
                    if req.type == 'video' and f.get('vcodec') != 'none':
                        label = f"{f.get('resolution', 'Unknown')} ({f.get('ext')}) - {f.get('format_note', '')}"
                        formats.append({
                            'format_id': f['format_id'],
                            'label': label,
                            'ext': f['ext'],
                            'filesize': f.get('filesize', 0),
                            'quality': 'good' 
                        })
                    # Audio
                    elif req.type == 'audio' and f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        # Estimate quality from ABR
                        abr = f.get('abr', 0)
                        q_tag = 'fair'
                        if abr >= 128: q_tag = 'good'
                        if abr >= 192: q_tag = 'excellent'
                        
                        label = f"{int(abr)}kbps ({f.get('ext')})"
                        formats.append({
                            'format_id': f['format_id'],
                            'label': label,
                            'ext': f['ext'],
                            'quality': q_tag
                        })
            
            # Sort: Best quality first
            formats.reverse()
            return {"formats": formats, "title": info.get('title', 'Video')}
            
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/download")
async def download_video(req: DownloadRequest):
    # Streaming Download
    # For audio, we might need to instruct yt-dlp to extract-audio pipe?
    # Streaming conversion is tricky. 
    # Best reliable way for spaces: Download standard format to stdout.
    
    cmd = [
        "yt-dlp", 
        "--force-ipv4",
        "-f", req.format_id,
        "-o", "-", # Pipe to stdout
        req.url
    ]
    
    # If audio requested and we want MP3 conversion, piping is complex because 
    # yt-dlp can't easily pipe converted output.
    # We will just download the raw stream requested (e.g. m4a/opus) 
    # Frontend handles naming it .mp3? No, better serve real file.
    # For now, simplistic streaming of the Source Format selected.
    
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
        # Fetch Real Metadata using Format ID
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(req.url, download=False)
            
            # Find specific format
            tgt_format = next((f for f in info['formats'] if f['format_id'] == req.format_id), None)
            
            if not tgt_format:
                return {"error": "Format not found"}
                
            abr = tgt_format.get('abr', 0)
            asr = tgt_format.get('asr', 0)
            acodec = tgt_format.get('acodec', 'unknown')
            
            quality = "fair"
            if abr >= 128: quality = "good"
            if abr >= 160: quality = "excellent"
            
            return {
                "analysis": {
                    "quality": quality,
                    "bitrate": f"{int(abr)} kbps (Variable)",
                    "sample_rate": f"{int(asr)} Hz",
                    "codec": acodec,
                    "distortion": "Not checked (Requires full download)" 
                }
            }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
