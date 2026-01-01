import gradio as gr
import yt_dlp
import tempfile
import os

def get_formats(url, media_type):
    """Fetch available formats for a URL"""
    if not url:
        return gr.update(choices=[], value=None), "⚠️ Please enter a URL"
    
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            if 'formats' in info:
                for f in info['formats']:
                    if media_type == 'video' and f.get('vcodec') != 'none':
                        abr = f.get('abr', 0) or 0
                        vbr = f.get('vbr', 0) or 0
                        label = f"{f.get('resolution', 'N/A')} ({f.get('ext')}) - {f.get('format_note', '')}"
                        formats.append((label, f['format_id']))
                    elif media_type == 'audio' and f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        abr = f.get('abr', 0) or 0
                        label = f"{int(abr)}kbps ({f.get('ext')})"
                        formats.append((label, f['format_id']))
            
            formats.reverse()  # Best first
            title = info.get('title', 'Video')
            return gr.update(choices=formats, value=formats[0][1] if formats else None), f"✅ Found {len(formats)} formats for: {title}"
            
    except Exception as e:
        return gr.update(choices=[], value=None), f"❌ Error: {str(e)}"

def analyze_format(url, format_id):
    """Analyze audio quality of a format"""
    if not url or not format_id:
        return "⚠️ Please search for formats first"
    
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            tgt = next((f for f in info['formats'] if f['format_id'] == format_id), None)
            
            if not tgt:
                return "❌ Format not found"
            
            abr = tgt.get('abr', 0) or 0
            asr = tgt.get('asr', 0) or 0
            acodec = tgt.get('acodec', 'unknown')
            
            quality = "Fair"
            if abr >= 128: quality = "Good"
            if abr >= 192: quality = "Excellent"
            
            return f"""
📊 **Audio Analysis**
- **Bitrate:** {int(abr)} kbps
- **Sample Rate:** {int(asr)} Hz
- **Codec:** {acodec}
- **Quality:** {quality}
"""
    except Exception as e:
        return f"❌ Error: {str(e)}"

def download_media(url, format_id, media_type):
    """Download the selected format"""
    if not url or not format_id:
        return None, "⚠️ Please search and select a format first"
    
    try:
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')
        
        ydl_opts = {
            'format': format_id,
            'outtmpl': output_template,
            'quiet': True,
        }
        
        # For audio, extract and convert to mp3
        if media_type == 'audio':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the downloaded file
        files = os.listdir(temp_dir)
        if files:
            filepath = os.path.join(temp_dir, files[0])
            return filepath, f"✅ Download Complete: {files[0]}"
        else:
            return None, "❌ Download failed"
            
    except Exception as e:
        return None, f"❌ Error: {str(e)}"

# Build UI
with gr.Blocks(theme=gr.themes.Soft(), title="ytDownloader") as app:
    gr.Markdown("""
    # ⬇️ ytDownloader
    ### Download True HQ Audio & Video from YouTube
    """)
    
    with gr.Row():
        url_input = gr.Textbox(label="YouTube URL", placeholder="https://www.youtube.com/watch?v=...", scale=3)
        media_type = gr.Radio(["video", "audio"], label="Type", value="video", scale=1)
    
    search_btn = gr.Button("🔍 Search Formats", variant="primary")
    status_box = gr.Markdown("Enter a URL and click Search")
    
    format_dropdown = gr.Dropdown(label="Select Format", choices=[], interactive=True)
    
    with gr.Row():
        analyze_btn = gr.Button("📊 Analyze Quality")
        download_btn = gr.Button("⬇️ Download", variant="primary")
    
    analysis_box = gr.Markdown("")
    download_output = gr.File(label="Downloaded File")
    download_status = gr.Markdown("")
    
    # Events
    search_btn.click(
        fn=get_formats,
        inputs=[url_input, media_type],
        outputs=[format_dropdown, status_box]
    )
    
    analyze_btn.click(
        fn=analyze_format,
        inputs=[url_input, format_dropdown],
        outputs=[analysis_box]
    )
    
    download_btn.click(
        fn=download_media,
        inputs=[url_input, format_dropdown, media_type],
        outputs=[download_output, download_status]
    )
    
    gr.Markdown("---\n*Powered by yt-dlp • Portfolio Project @yepzhi*")

if __name__ == "__main__":
    app.launch()
