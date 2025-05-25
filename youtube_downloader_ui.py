import gradio as gr
import os
import tempfile
from pytubefix import YouTube
from pytubefix.cli import on_progress
from pathlib import Path

def download_single_video(url, quality, progress=gr.Progress()):
    """Download a single YouTube video"""
    if not url.strip():
        return "Please provide a valid YouTube URL", None, ""
    
    try:
        progress(0.1, desc="Connecting to YouTube...")
        yt = YouTube(url, on_progress_callback=on_progress)
        
        progress(0.3, desc="Getting video information...")
        title = yt.title
        
        # Create temporary directory for download
        temp_dir = tempfile.mkdtemp()
        
        progress(0.5, desc="Selecting video stream...")
        
        # Try to get the exact quality requested
        if quality == 'highest':
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        else:
            stream = yt.streams.filter(progressive=True, file_extension='mp4', res=quality).first()
            if not stream:
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        if not stream:
            return f"No suitable stream found for {title}", None, ""
        
        progress(0.7, desc="Downloading video...")
        
        # Clean filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title}.mp4"
        
        # Download the video
        downloaded_file = stream.download(output_path=temp_dir, filename=filename)
        
        progress(1.0, desc="Download completed!")
        
        return f"✓ Successfully downloaded: {title}\nQuality: {stream.resolution}", downloaded_file, f"Downloaded: {title}"
        
    except Exception as e:
        return f"✗ Error downloading video: {str(e)}", None, ""

# Create Gradio interface
with gr.Blocks(title="YouTube Video Downloader", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎥 YouTube Video Downloader
    
    Download YouTube videos from a single URL.
    """)
    
    with gr.Row():
        url_input = gr.Textbox(
            label="YouTube URL (Paste any YouTube URL - regular videos or Shorts)",
            placeholder="https://www.youtube.com/watch?v=...",
        )
    
    with gr.Row():
        quality_input = gr.Dropdown(
            choices=["highest", "720p", "480p", "360p", "240p", "144p"],
            value="720p",
            label="Video Quality"
        )
    
    download_btn = gr.Button("🚀 Start Download", variant="primary", size="lg")
    
    with gr.Row():
        with gr.Column():
            status_output = gr.Textbox(
                label="Download Status",
                lines=8,
                max_lines=10,
                interactive=False
            )
        
        with gr.Column():
            download_file = gr.File(
                label="Download Completed Files",
                visible=True
            )
            
            download_info = gr.Textbox(
                label="Download Info",
                interactive=False,
                visible=False
            )
    
    # Event handler
    download_btn.click(
        fn=download_single_video,
        inputs=[url_input, quality_input],
        outputs=[status_output, download_file, download_info]
    )
    
    # Usage instructions
    with gr.Accordion("Usage Instructions", open=False):
        gr.Markdown("""
        ### How to use:
        1. Paste any YouTube URL in the input field
        2. Choose your preferred video quality
        3. Click "Start Download"
        
        ### Notes:
        - Supports both regular YouTube videos and YouTube Shorts
        - If requested quality isn't available, the highest available quality is downloaded
        - Downloaded file will be available for download once complete
        """)

# Launch the app
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
