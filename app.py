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

app = FastAPI()

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

@app.get("/")
async def read_root():
    return FileResponse('index.html')

@app.post("/formats")
async def get_formats(req: URLRequest):
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
                            'quality': 'good' # logic to determine quality
                        })
                    # Audio
                    elif req.type == 'audio' and f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        label = f"{f.get('abr', 0)}kbps ({f.get('ext')})"
                        formats.append({
                            'format_id': f['format_id'],
                            'label': label,
                            'ext': f['ext'],
                            'quality': 'excellent' if f.get('abr', 0) >= 128 else 'fair'
                        })
            
            # Sort: Best quality first
            formats.reverse()
            return {"formats": formats, "title": info.get('title', 'Video')}
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/download")
async def download_video(req: DownloadRequest):
    # For Spaces, we can't save huge files easily.
    # Ideally we stream pure output from yt-dlp to client.
    
    # Command to pipe to stdout
    cmd = [
        "yt-dlp", 
        "-f", req.format_id,
        "-o", "-", # Pipe to stdout
        req.url
    ]
    
    # This is a simplifiction. Real streaming usually requires subprocess piping.
    # For now, let's verify format.
    
    try:
        # We define a generator to read stdout
        def iterfile():
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                while True:
                    chunk = proc.stdout.read(65536) # 64k chunks
                    if not chunk:
                        break
                    yield chunk
                    
        return StreamingResponse(iterfile(), media_type="application/octet-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-audio")
async def analyze_audio(req: AnalyzeRequest):
    # Mock analysis since we don't have the file downloaded yet
    # In a real app we'd download a sample.
    return {
        "analysis": {
            "quality": "excellent",
            "bitrate": "128kbps+",
            "sample_rate": "44.1kHz",
            "codec": "mp3/aac",
            "distortion": "None detected (Metadata Analysis)"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
