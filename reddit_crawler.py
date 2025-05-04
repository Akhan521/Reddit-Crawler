
'''
This is a Reddit crawler script that uses the PRAW (Python Reddit API Wrapper) library to scrape posts from
specified subreddits. It allows the user to also filter posts by keywords. Additionally, the user can specify the
amount of data to scrape in MB. All scraped data is saved in JSON files (each ~10MB). 

To avoid duplicate data, the script checks for existing posts and only saves new ones.
'''
import praw
import json
import os
import time
import requests
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import argparse

# Set up command line argument parsing.
def parse_arguments():
    parser = argparse.ArgumentParser(description='Reddit Crawler')
    parser.add_argument('subreddits_file', help='File containing list of subreddits to scrape (one per line)')
    parser.add_argument('keywords_file', help='File containing keywords to filter posts (one per line)')
    parser.add_argument('output_dir', default='reddit_data', help='Directory to save scraped data')
    parser.add_argument('target_size_mb', type=float, help='Target data size in MB')
    return parser.parse_args()

# Title extraction function.
def extract_page_title(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        # If we have a successful (200) response, parse the HTML if we have an HTML page.
        if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
            # Use BeautifulSoup to parse the HTML and extract the title.
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else 'No Title'
            return title
        else:
            return None
    except requests.RequestException as e:
        print(f"Error fetching page title: {e}")
        return None

# Save posts to a JSON file.
def save_posts(posts, file_index, output_dir):
    # Create the output directory if it doesn't exist.
    os.makedirs(output_dir, exist_ok=True)

    # Our filepath:
    filepath = os.path.join(output_dir, f'reddit_posts_{file_index}.json')

    # Save the posts to a JSON file.
    with open(filepath, 'w', encoding='utf-8') as f:
        for post in posts:
            f.write(json.dumps(post, ensure_ascii=False) + '\n')

    # Return the file size.
    return os.path.getsize(filepath)

# Function to load subreddits from a subreddits file.
def load_subreddits(file_path):
    try:
        with open(file_path, 'r') as f:
            subreddits = [line.strip() for line in f if line.strip()]
        if not subreddits:
            raise ValueError("No subreddits found in the file.")
        return subreddits
    except FileNotFoundError:
        raise FileNotFoundError(f"Subreddits file '{file_path}' not found.")

# Function to load keywords from a keywords file.
def load_keywords(file_path):
    try:
        with open(file_path, 'r') as f:
            keywords = [line.strip() for line in f if line.strip()]
        if not keywords:
            raise ValueError("No keywords found in the file.")
        return keywords
    except FileNotFoundError:
        raise FileNotFoundError(f"Keywords file '{file_path}' not found.")
    
# Function to load existing posts so we can check for duplicate posts
def load_existing_post_ids(output_dir):
    seen_ids = set()
    for filename in os.listdir(output_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        post = json.loads(line)
                        seen_ids.add(post['id'])
                    except json.JSONDecodeError:
                        continue
    return seen_ids

# Main function to scrape Reddit posts.
def scrape_reddit():
    # Parse command line arguments.
    args = parse_arguments()
    subreddits_file = args.subreddits_file
    keywords_file = args.keywords_file
    output_dir = args.output_dir
    target_size_mb = args.target_size_mb
    target_size_bytes = target_size_mb * 1024 * 1024  # Convert MB to bytes.

    # Load subreddits and keywords from files.
    subreddits = load_subreddits(subreddits_file)
    keywords = load_keywords(keywords_file)
    print(f"Loaded {len(subreddits)} subreddits and {len(keywords)} keywords.")

    # Initialize the Reddit API client using our praw.ini file.
    reddit = praw.Reddit("DEFAULT")

    # Create the output directory if it doesn't exist.
    os.makedirs(output_dir, exist_ok=True)

    # Initialize variables.
    current_posts = []
    file_index = 1
    total_size = 0
    post_limit = 100  # Limit for the number of posts to scrape from each subreddit per stream (e.g. hot, new, etc.)
    streams = ['hot']  # Streams to scrape from.

    # Initialize Set for hashing post ID's with existing data if it exists
    seen_ids = load_existing_post_ids(output_dir)

    print(f"Scraping started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Iterate through each subreddit.
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name.strip())

        # Scrape posts from multiple streams (hot, new, top).
        for stream in streams:
            print(f"Scraping {stream} posts from r/{subreddit_name.strip()}...")

            # Scrape posts from the specified stream.
            for post in getattr(subreddit, stream)(limit=post_limit):
                # If we've reached the target size, we can stop.
                if total_size >= target_size_bytes:
                    print(f"Target size of {target_size_mb} MB reached. Stopping scraping.")
                    break

                # Otherwise, check if the post contains any of the keywords.
                content = post.title.lower() + ' ' + post.selftext.lower()
                if any(keyword.lower() in content for keyword in keywords):
                    # Extract the page title if the post has a URL.
                    if isinstance(post.url, str) and post.url and not post.url.endswith(('.jpg', '.png', '.gif')):
                        page_title = extract_page_title(post.url)
                        # Add a delay to avoid overwhelming the server.
                        time.sleep(1)

                    # Don't append post if post ID is already in hash
                    if post.id in seen_ids:
                        continue
                    
                    # Create a dictionary to store the post data.
                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'selftext': post.selftext,
                        'url': post.url,
                        'subreddit': str(post.subreddit),
                        'score': post.score,
                        'upvote_ratio': post.upvote_ratio,
                        'page_title': page_title if post.url else None,
                    }

                    # Append the post data to the current posts list.
                    current_posts.append(post_data)

                    # Can maybe add another way to look at duplicate? Like looking at title and seeing if similar?
                    # Add post ID to hash if visited already
                    seen_ids.add(post.id)

                    # Check file size and save if necessary (~10MB).
                    if len(current_posts) >= 100:
                        file_size = save_posts(current_posts, file_index, output_dir)
                        total_size += file_size
                        print(f"Saved {len(current_posts)} posts to reddit_posts_{file_index}.json' ({file_size / (1024 * 1024):.2f} MB)")
                        current_posts = []
                        file_index += 1

            # If we reached the target size, break out of the loop.
            if total_size >= target_size_bytes:
                break

        # If we reached the target size, break out of the outer loop.
        if total_size >= target_size_bytes:
            break

    # If there are any remaining posts, save them.
    if current_posts:
        file_size = save_posts(current_posts, file_index, output_dir)
        total_size += file_size
        print(f"Saved {len(current_posts)} posts to reddit_posts_{file_index}.json' ({file_size / (1024 * 1024):.2f} MB)")

    # Print the total size of the scraped data.
    print(f"Total size of scraped data: {total_size / (1024 * 1024):.2f} MB")
    print(f"Scraping finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # Call our scrape_reddit function to start the scraping process.
    scrape_reddit()