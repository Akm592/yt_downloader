import gradio as gr
import csv
import os
import tempfile
import zipfile
from pytubefix import YouTube
from pytubefix.cli import on_progress
import pandas as pd
from pathlib import Path
import shutil

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

def process_csv_download(csv_file, quality, num_videos, progress=gr.Progress()):
    """Process CSV file and download multiple videos"""
    if csv_file is None:
        return "Please upload a CSV file", None, ""
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file.name)
        
        if 'url' not in df.columns:
            return "CSV file must contain a 'url' column", None, ""
        
        # Get valid URLs
        valid_urls = df[df['url'].notna() & (df['url'] != '')]['url'].tolist()
        
        if not valid_urls:
            return "No valid URLs found in CSV file", None, ""
        
        # Limit number of videos
        if num_videos == "all":
            urls_to_download = valid_urls
        else:
            urls_to_download = valid_urls[:int(num_videos)]
        
        # Create temporary directory for downloads
        temp_dir = tempfile.mkdtemp()
        download_dir = os.path.join(temp_dir, "downloaded_videos")
        os.makedirs(download_dir, exist_ok=True)
        
        successful_downloads = 0
        failed_downloads = 0
        downloaded_files = []
        
        total_videos = len(urls_to_download)
        
        for i, url in enumerate(urls_to_download):
            try:
                progress((i + 1) / total_videos, desc=f"Downloading video {i+1}/{total_videos}")
                
                yt = YouTube(url)
                
                # Get video ID if available
                video_id = df[df['url'] == url]['Video_id'].iloc[0] if 'Video_id' in df.columns else f"video_{i+1}"
                
                # Select stream
                if quality == 'highest':
                    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                else:
                    stream = yt.streams.filter(progressive=True, file_extension='mp4', res=quality).first()
                    if not stream:
                        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                
                if stream:
                    # Clean filename
                    safe_title = "".join(c for c in yt.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"{video_id}_{safe_title}.mp4"
                    
                    downloaded_file = stream.download(output_path=download_dir, filename=filename)
                    downloaded_files.append(downloaded_file)
                    successful_downloads += 1
                else:
                    failed_downloads += 1
                    
            except Exception as e:
                failed_downloads += 1
                continue
        
        # Create zip file if multiple videos
        if len(downloaded_files) > 1:
            zip_path = os.path.join(temp_dir, "downloaded_videos.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_path in downloaded_files:
                    zipf.write(file_path, os.path.basename(file_path))
            
            summary = f"""
📊 DOWNLOAD SUMMARY:
✅ Successful downloads: {successful_downloads}
❌ Failed downloads: {failed_downloads}
📁 Total videos processed: {total_videos}
            """
            
            return summary, zip_path, f"Downloaded {successful_downloads} videos"
            
        elif len(downloaded_files) == 1:
            summary = f"""
📊 DOWNLOAD SUMMARY:
✅ Successful downloads: {successful_downloads}
❌ Failed downloads: {failed_downloads}
📁 Total videos processed: {total_videos}
            """
            return summary, downloaded_files[0], f"Downloaded {successful_downloads} video"
        else:
            return f"❌ All {total_videos} downloads failed", None, ""
            
    except Exception as e:
        return f"Error processing CSV file: {str(e)}", None, ""

def update_num_videos_visibility(download_type):
    """Show/hide number of videos input based on download type"""
    if download_type == "Single URL":
        return gr.update(visible=False)
    else:
        return gr.update(visible=True)

def update_input_visibility(download_type):
    """Show/hide input components based on download type"""
    if download_type == "Single URL":
        return gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=True)

# Create Gradio interface
with gr.Blocks(title="YouTube Video Downloader", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎥 YouTube Video Downloader
    
    Download YouTube videos either from a single URL or bulk download from a CSV file.
    
    **CSV Format Required:**
    ```
    Video_id,url,tag,sentiment,emotion,humor,toxic,sarcasm,language
    video1,https://www.youtube.com/watch?v=example1,tag1,positive,happy,yes,no,no,en
    ```
    """)
    
    with gr.Row():
        download_type = gr.Radio(
            choices=["Single URL", "CSV File"],
            value="Single URL",
            label="Download Type"
        )
    
    with gr.Row():
        # Single URL input
        url_input = gr.Textbox(
            label="YouTube URL (Paste any YouTube URL - regular videos or Shorts)",
            placeholder="https://www.youtube.com/watch?v=...",
            visible=True
        )
        
        # CSV file input
        csv_input = gr.File(
            label="Upload CSV File (Must contain 'url' column)",
            file_types=[".csv"],
            visible=False
        )
    
    with gr.Row():
        quality_input = gr.Dropdown(
            choices=["highest", "720p", "480p", "360p", "240p", "144p"],
            value="720p",
            label="Video Quality"
        )
        
        num_videos_input = gr.Dropdown(
            choices=["1", "5", "10", "20", "50", "all"],
            value="5",
            label="Number of Videos to Download (CSV mode only)",
            visible=False
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
    
    # Event handlers
    download_type.change(
        fn=update_input_visibility,
        inputs=[download_type],
        outputs=[url_input, csv_input]
    )
    
    download_type.change(
        fn=update_num_videos_visibility,
        inputs=[download_type],
        outputs=[num_videos_input]
    )
    
    def handle_download(download_type, url, csv_file, quality, num_videos):
        if download_type == "Single URL":
            return download_single_video(url, quality)
        else:
            return process_csv_download(csv_file, quality, num_videos)
    
    download_btn.click(
        fn=handle_download,
        inputs=[download_type, url_input, csv_input, quality_input, num_videos_input],
        outputs=[status_output, download_file, download_info]
    )
    
    # Examples section
    gr.Markdown("## 📋 Examples")
    
    with gr.Accordion("Example CSV Format", open=False):
        gr.Code("""Video_id,url,tag,sentiment,emotion,humor,toxic,sarcasm,language
video1,https://www.youtube.com/watch?v=dQw4w9WgXcQ,music,positive,happy,yes,no,no,en
video2,https://www.youtube.com/shorts/abcd1234,comedy,positive,funny,yes,no,yes,en
video3,https://youtu.be/example123,educational,neutral,calm,no,no,no,en""", language="csv")
    
    with gr.Accordion("Usage Instructions", open=False):
        gr.Markdown("""
        ### Single URL Mode:
        1. Select "Single URL" option
        2. Paste any YouTube URL
        3. Choose video quality
        4. Click "Start Download"
        
        ### CSV File Mode:
        1. Select "CSV File" option
        2. Upload your CSV file with YouTube URLs
        3. Choose how many videos to download
        4. Select video quality
        5. Click "Start Download"
        
        ### Notes:
        - Supports both regular YouTube videos and YouTube Shorts
        - CSV files are processed and multiple videos are zipped together
        - If requested quality isn't available, the highest available quality is downloaded
        - Failed downloads are skipped and reported in the summary
        """)

# Launch the app
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
