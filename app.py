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
                        height = f.get('height', 0) or 0
                        label = f"{f.get('resolution', 'Unknown')} ({f.get('ext')}) - {f.get('format_note', '')}"
                        formats.append({
                            'format_id': f['format_id'],
                            'label': label,
                            'ext': f['ext'],
                            'filesize': f.get('filesize', 0),
                            'quality': 'good',
                            'height': height  # For sorting
                        })
                    elif req.type == 'audio' and f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        abr = f.get('abr', 0) or 0
                        acodec = f.get('acodec', 'unknown')
                        
                        # Opus often reports 0 bitrate but is actually ~160kbps
                        if 'opus' in acodec.lower() and abr == 0:
                            abr = 160  # Assign realistic value
                        
                        q_tag = 'fair'
                        if abr >= 128: q_tag = 'good'
                        if abr >= 160 or 'opus' in acodec.lower(): q_tag = 'excellent'
                        
                        label = f"{int(abr)}kbps ({f.get('ext')}) - {acodec}"
                        formats.append({
                            'format_id': f['format_id'],
                            'label': label,
                            'ext': f['ext'],
                            'quality': q_tag,
                            'abr': abr  # For sorting
                        })
            
            # Sort: Video by height, Audio by bitrate (highest first)
            if req.type == 'video':
                formats.sort(key=lambda x: x.get('height', 0), reverse=True)
            else:
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
    import tempfile
    import os
    import glob
    
    try:
        # For audio: download best and convert to MP3
        if req.type == 'audio':
            temp_dir = tempfile.mkdtemp()
            output_template = os.path.join(temp_dir, 'audio')
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '0',  # VBR best quality (~192-256kbps, honest)
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([req.url])
            
            # Find the MP3 file
            mp3_files = glob.glob(os.path.join(temp_dir, '*.mp3'))
            if mp3_files:
                filepath = mp3_files[0]
                
                def iterfile():
                    with open(filepath, 'rb') as f:
                        while chunk := f.read(65536):
                            yield chunk
                    # Cleanup after streaming
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                
                return StreamingResponse(
                    iterfile(), 
                    media_type="audio/mpeg",
                    headers={"Content-Disposition": "attachment; filename=audio.mp3"}
                )
            else:
                raise HTTPException(status_code=500, detail="MP3 conversion failed")
        
        else:
            # Video: stream directly
            cmd = [
                "yt-dlp", 
                "-f", req.format_id,
                "-o", "-",
                req.url
            ]
            
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
