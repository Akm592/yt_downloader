import csv
import os
from pytubefix import YouTube
from pytubefix.cli import on_progress
import sys

def download_video(url, quality, download_path, video_id):
    """Download a single YouTube video using pytubefix"""
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        print(f"Downloading: {yt.title}")
        
        # Try to get the exact quality requested
        stream = yt.streams.filter(progressive=True, file_extension='mp4', res=quality).first()
        
        # If exact quality not available, get the highest available
        if not stream:
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            if stream:
                print(f"Requested quality {quality} not available. Downloading in {stream.resolution}")
            else:
                # For Shorts, try adaptive streams
                stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').desc().first()
                if stream:
                    print(f"Using adaptive stream: {stream.resolution}")
        
        # Create filename with video_id prefix
        filename = f"{video_id}_{yt.title}"
        # Remove invalid characters for filename
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # Download the video
        stream.download(output_path=download_path, filename=filename + '.mp4')
        print(f"✓ Successfully downloaded: {filename}")
        return True
        
    except Exception as e:
        print(f"✗ Error downloading {url}: {str(e)}")
        return False

def main():
    print("=== YouTube Video Downloader from CSV (Fixed Version) ===\n")
    
    # Get CSV file path from user
    csv_file = input("Enter the path to your CSV file: ").strip()
    
    if not os.path.exists(csv_file):
        print("Error: CSV file not found!")
        return
    
    # Read CSV file and extract URLs
    video_data = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if 'url' in row and row['url'].strip():
                    video_data.append({
                        'video_id': row.get('Video_id', ''),
                        'url': row['url'].strip()
                    })
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return
    
    if not video_data:
        print("No valid URLs found in the CSV file!")
        return
    
    print(f"Found {len(video_data)} video URLs in the CSV file.")
    
    # Get number of videos to download
    max_videos = len(video_data)
    while True:
        try:
            num_videos = input(f"How many videos do you want to download? (1-{max_videos}, or 'all'): ").strip()
            if num_videos.lower() == 'all':
                num_videos = max_videos
                break
            else:
                num_videos = int(num_videos)
                if 1 <= num_videos <= max_videos:
                    break
                else:
                    print(f"Please enter a number between 1 and {max_videos}")
        except ValueError:
            print("Please enter a valid number or 'all'")
    
    # Get quality preference
    print("Available quality options: 720p, 480p, 360p, 240p, 144p, highest")
    while True:
        quality = input("Enter preferred video quality (e.g., 720p, 480p, 360p, or 'highest'): ").strip()
        if quality.lower() in ['highest', 'best']:
            quality = 'highest'
            break
        elif quality in ['720p', '480p', '360p', '240p', '144p']:
            break
        else:
            print("Please enter a valid quality (e.g., 720p, 480p, 360p, 240p, 144p, or 'highest')")
    
    # Create download directory
    download_path = "downloaded_videos"
    if not os.path.exists(download_path):
        os.makedirs(download_path)
        print(f"Created download directory: {download_path}")
    
    # Download videos
    print(f"\nStarting download of {num_videos} videos...")
    print("=" * 50)
    
    successful_downloads = 0
    failed_downloads = 0
    
    for i, video in enumerate(video_data[:num_videos]):
        print(f"\nProgress: {i+1}/{num_videos}")
        
        success = download_video(video['url'], quality, download_path, video['video_id'])
        
        if success:
            successful_downloads += 1
        else:
            failed_downloads += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("DOWNLOAD SUMMARY")
    print("=" * 50)
    print(f"Total videos processed: {num_videos}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Videos saved to: {os.path.abspath(download_path)}")

if __name__ == "__main__":
    main()
