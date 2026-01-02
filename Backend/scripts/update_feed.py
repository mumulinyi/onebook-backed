import json
import os
import requests
from datetime import datetime
import time

# Configuration
DATA_DIR = "Backend/data"
OUTPUT_DIR = "Backend/public"
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
FEED_FILE = os.path.join(OUTPUT_DIR, "feed.json")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
