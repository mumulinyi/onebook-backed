import json
import os
import requests
from datetime import datetime
import time
import yt_dlp

# Configuration
DATA_DIR = "Backend/data"
OUTPUT_DIR = "Backend/public"
SUBTITLES_DIR = os.path.join(OUTPUT_DIR, "subtitles")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
FEED_FILE = os.path.join(OUTPUT_DIR, "feed.json")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SUBTITLES_DIR, exist_ok=True)

def download_subtitles(video_id):
    """
    Downloads subtitles for a video using yt-dlp.
    Returns the relative path to the subtitle file if successful, else None.
    """
    # Expected file path (yt-dlp names it [id].en.vtt by default when requesting 'en')
    # Note: yt-dlp might use 'en-orig' or other variants depending on availability,
    # but forcing 'vtt' and specific naming template helps.
    
    # We'll check for the file first to avoid re-downloading
    expected_filename = f"{video_id}.en.vtt"
    full_path = os.path.join(SUBTITLES_DIR, expected_filename)
    
    if os.path.exists(full_path):
        return f"subtitles/{expected_filename}"

    print(f"Downloading subtitles for {video_id}...")
    
    # Check for cookies in environment variable
    cookies_content = os.environ.get("YOUTUBE_COOKIES")
    cookie_file = "cookies.txt"
    if cookies_content:
        # Create a temporary cookies file
        with open(cookie_file, "w") as f:
            f.write(cookies_content)
    
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        # Change from strict 'en' to regex 'en.*' to match en-US, en-GB, etc.
        'subtitleslangs': ['en.*'],
        'subtitlesformat': 'vtt',
        # Force filename to be just the ID (yt-dlp will append .en.vtt or .en-US.vtt)
        'outtmpl': os.path.join(SUBTITLES_DIR, '%(id)s'),
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }
    
    if cookies_content:
        ydl_opts['cookiefile'] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            
        # Clean up cookie file
        if cookies_content and os.path.exists(cookie_file):
            os.remove(cookie_file)
            
        # Check if the file exists now
        if os.path.exists(full_path):
            print(f"Subtitle downloaded: {expected_filename}")
            return f"subtitles/{expected_filename}"
        else:
            # Sometimes it might be just .vtt if no language code is appended (rare with explicit lang)
            # or it might have downloaded a different language code if 'en' wasn't exact match?
            # Let's simple-check directory for any file starting with video_id
            for f in os.listdir(SUBTITLES_DIR):
                if f.startswith(video_id) and f.endswith(".vtt"):
                    return f"subtitles/{f}"
                    
    except Exception as e:
        print(f"Failed to download subtitles for {video_id}: {e}")
    
    return None

def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        return []
    with open(CHANNELS_FILE, 'r') as f:
        return json.load(f)

def get_uploads_playlist_id(channel_id):
    # The uploads playlist ID is usually the channel ID with 'UC' replaced by 'UU'
    if channel_id.startswith("UC"):
        return "UU" + channel_id[2:]
    return channel_id

def fetch_videos_from_playlist(playlist_id, api_key, max_results=50):
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    videos = []
    next_page_token = None
    
    # Fetch up to max_results (e.g. 50, or multiple pages if needed)
    # Here we just fetch one page of 50 for efficiency, but you can loop if you want more history.
    # To save quota, one call (50 videos) per channel is usually enough for "updates".
    # If you want FULL history, you can loop. Let's loop to get up to 100 for now.
    
    total_fetched = 0
    fetch_limit = 100 # Adjust this based on your needs
    
    while total_fetched < fetch_limit:
        params = {
            'part': 'snippet',
            'playlistId': playlist_id,
            'maxResults': 50,
            'key': api_key
        }
        if next_page_token:
            params['pageToken'] = next_page_token
            
        try:
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code != 200:
                print(f"Error fetching playlist {playlist_id}: {response.text}")
                break
                
            data = response.json()
            items = data.get('items', [])
            
            for item in items:
                snippet = item.get('snippet', {})
                resourceId = snippet.get('resourceId', {})
                
                # Extract high quality thumbnail if available, else medium, else default
                thumbnails = snippet.get('thumbnails', {})
                thumb_url = thumbnails.get('high', {}).get('url') or \
                            thumbnails.get('medium', {}).get('url') or \
                            thumbnails.get('default', {}).get('url') or ""
                
                video = {
                    "id": resourceId.get('videoId'),
                    "title": snippet.get('title'),
                    "published": snippet.get('publishedAt'), # ISO 8601 format
                    "thumbnail": thumb_url,
                    "description": snippet.get('description'),
                    "channelId": snippet.get('channelId'),
                    "channelTitle": snippet.get('channelTitle')
                }
                
                # Fetch subtitles (added)
                subtitle_path = download_subtitles(video["id"])
                if subtitle_path:
                    video["subtitleUrl"] = subtitle_path
                
                videos.append(video)
            
            total_fetched += len(items)
            next_page_token = data.get('nextPageToken')
            
            if not next_page_token:
                break
                
        except Exception as e:
            print(f"Exception fetching playlist {playlist_id}: {e}")
            break
            
    return videos

def main():
    print("Starting Content Update (Official API Mode)...")
    
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("Error: YOUTUBE_API_KEY environment variable not set.")
        # We don't exit here to avoid breaking the workflow if it's just a local test,
        # but in production this will result in empty updates if not set.
        return

    channels = load_channels()
    all_videos = {}
    
    # 1. Load existing feed to preserve history (optional, but good practice)
    if os.path.exists(FEED_FILE):
        try:
            with open(FEED_FILE, 'r') as f:
                old_feed = json.load(f)
                for v in old_feed:
                    all_videos[v['id']] = v
        except:
            pass
    
    # 2. Fetch new videos
    for channel in channels:
        cid = channel['id']
        cname = channel['name']
        print(f"Fetching videos for {cname} ({cid})...")
        
        playlist_id = get_uploads_playlist_id(cid)
        new_videos = fetch_videos_from_playlist(playlist_id, api_key)
        
        print(f"  - Found {len(new_videos)} videos")
        
        for v in new_videos:
            all_videos[v['id']] = v
            
    # 3. Sort and Save
    final_list = list(all_videos.values())
    # Sort by published date descending
    final_list.sort(key=lambda x: x['published'], reverse=True)
    
    # Keep reasonable limit (e.g. latest 1000)
    final_list = final_list[:1000]
    
    with open(FEED_FILE, 'w') as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)
        
    print(f"Update Complete. Total videos in feed: {len(final_list)}")

if __name__ == "__main__":
    main()
