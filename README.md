# Zero-Cost Content Backend

This directory contains a complete, zero-cost backend solution for OneBook using GitHub Actions and GitHub Pages.

## How it works
1. **Config**: You add YouTube Channel IDs to `data/channels.json`.
2. **Fetch**: The `scripts/update_feed.py` script runs (via GitHub Actions).
   - It fetches the latest videos from each channel's RSS feed.
   - It automatically downloads subtitles for each new video.
   - It generates a master `feed.json` and individual subtitle files.
3. **Serve**: The data is committed back to the repo and served via GitHub's raw file network (or GitHub Pages).

## Setup Guide

1. **Push to GitHub**:
   Ensure this `Backend` folder is in your GitHub repository.

2. **Enable Permissions**:
   In your GitHub Repo Settings -> Actions -> General -> Workflow permissions:
   - Select "Read and write permissions" (so the Action can commit the new data back to the repo).

3. **Configure Channels**:
   Edit `Backend/data/channels.json` to add your desired YouTube channels.

4. **Update App Config**:
   Open `OneBook/Features/YoutubeReader/Services/YoutubeSubtitleService.swift`.
   Find `contentServerBaseURL` and update it to point to your repo:
   ```swift
   // Example
   private let contentServerBaseURL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/Backend/public"
   ```

5. **Run**:
   The workflow is scheduled to run every hour. You can also manually trigger it in the "Actions" tab.

## Directory Structure
- `data/`: Configuration files (channels).
- `public/`: The generated data (feed, subtitles). **Do not edit manually.**
- `scripts/`: The Python logic.
- `.github/workflows/`: The automation schedule.
