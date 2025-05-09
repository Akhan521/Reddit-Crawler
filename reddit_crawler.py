
'''
This is a Reddit crawler script that uses the PRAW (Python Reddit API Wrapper) library to scrape posts from
specified subreddits. It allows the user to also filter posts by keywords. Additionally, the user can specify the
amount of data to scrape in MB. All scraped data is saved in JSON files (each ~10MB). 

To avoid duplicate data, the script checks for existing posts and only saves new ones.
'''
import praw
import json
import os
import prawcore
import time
import requests
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import argparse
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# Set up command line argument parsing.
def parse_arguments():
    parser = argparse.ArgumentParser(description='Reddit Crawler')
    parser.add_argument('subreddits_file', help='File containing list of subreddits to scrape (one per line)')
    parser.add_argument('keywords_file', help='File containing keywords to filter posts (one per line)')
    parser.add_argument('output_dir', default='reddit_data', help='Directory to save scraped data')
    parser.add_argument('target_size_mb', type=float, help='Target data size in MB')
    return parser.parse_args()

# Set up a session with retries for HTTP requests.
def create_requests_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Title extraction function.
def extract_page_title(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # Create a session with retries.
        session = create_requests_session()
        response = session.get(url, headers=headers, timeout=15)
        # If we have a successful (200) response, parse the HTML if we have an HTML page.
        if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
            # Use BeautifulSoup to parse the HTML and extract the title.
            soup = BeautifulSoup(response.text, 'html.parser')
            if soup.title and soup.title.string:
                return soup.title.string.strip()
            return "No Title"
        return None
    except requests.RequestException as e:
        print(f"Error fetching page title: {e}")
        return None

# Extract URL using regex
def extract_urls(text): 
    url_regex = r'https?://[^\s)>"\'\]]+'
    return re.findall(url_regex, text)

# Enrich post with titles
def enrich_post_with_titles(post):
    selftext = post.get('selftext', '')
    urls = extract_urls(selftext)
    titles = []
    for url in urls:
        title = extract_page_title(url)
        if title:
            titles.append(title)
        time.sleep(3)  # Add delay to avoid overwhelming servers.
    if titles:
        post['linked_titles'] = titles
    return post

# Save posts to a JSON file.
def save_posts(posts, file_index, output_dir, title, target_size_bytes):
    # Create the output directory if it doesn't exist.
    os.makedirs(output_dir, exist_ok=True)

    # Our filepath:
    filepath = os.path.join(output_dir, f'reddit_posts_{title}_{file_index}.json')

    # Save the posts to a JSON file.
    # To ensure thread safety, we use a lock.
    with open(filepath, 'a', encoding='utf-8') as f:
        for post in posts:
            f.write(json.dumps(post, ensure_ascii=False) + '\n')

    file_size = os.path.getsize(filepath)
    # If we've reached our target size, we can stop all threads.
    with global_lock:
        global_size[0] += file_size
        if global_size[0] >= target_size_bytes:
            stop_flag[0] = True
    return file_size


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

# Custom Rate Limiter class to handle Reddit API rate limits.
class RateLimiter:
    def __init__(self, requests_per_min):
        self.requests_per_min = requests_per_min
        self.interval = 60.0 / requests_per_min # Time interval between requests in seconds.
        self.last_request_time = 0
        self.lock = Lock()

    def acquire(self):
        with self.lock:
            current_time = time.time()
            elapsed_time = current_time - self.last_request_time
            if elapsed_time < self.interval:
                # If we are within the rate limit, sleep for the remaining time.
                time.sleep(self.interval - elapsed_time)
            self.last_request_time = time.time()

# Threading: function to scrape a subreddit per thread.
def scrape_subreddit(subreddit_name, keywords, output_dir, target_size_bytes, seen_ids, rate_limiter):
    reddit = praw.Reddit("DEFAULT")
    current_posts = []
    total_size = 0 # Total size of scraped data.
    post_limit = 10000 # Limit for the number of posts to store in files.
    streams = ['hot', 'top', 'new', 'rising'] # Streams to scrape from.
    file_index = 1 # File index for saving posts.
    counter = 1 # Counter for the number of posts processed.
    
    try:
        # Acquire the rate limiter before making a request.
        rate_limiter.acquire()
        # Attempt to access the subreddit.
        subreddit = reddit.subreddit(subreddit_name.strip())
        rate_limiter.acquire()
        # Check if the subreddit is valid and accessible.
        next(subreddit.hot(limit=1)) 
    except (prawcore.exceptions.NotFound, prawcore.exceptions.Forbidden, prawcore.exceptions.Redirect) as e:
        print(f"Skipping invalid subreddit '{subreddit_name.strip()}': {e}")
        return 0
    except prawcore.exceptions.RequestException as e:
        print(f"Error accessing subreddit '{subreddit_name.strip()}': {e}")
        return 0

    # Set the title (to be used in our filename).
    title = subreddit_name.strip().replace('/', '_')

    # Scrape posts from multiple streams (hot, new, top).
    for stream in streams:
        print(f"Thread: scraping {stream} posts from r/{subreddit_name.strip()}...")
        try:
            # Acquire the rate limiter before making a request.
            rate_limiter.acquire()
            # Scrape posts from the subreddit stream.
            for post in getattr(subreddit, stream)(limit=None):
                counter += 1
                if counter % 100 == 0:
                    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Thread: processed {counter} posts from r/{subreddit_name.strip()}...")
                    time.sleep(1) # After every 100 posts, sleep for 1 second to avoid overwhelming the server.

                # Check if we should stop scraping.
                with global_lock:
                    if stop_flag[0]:
                        print(f"Thread: stopping scraping for r/{subreddit_name.strip()} due to reaching target size.")
                        return total_size

                content = post.title.lower() + ' ' + post.selftext.lower()
                if any(keyword.lower() in content for keyword in keywords):
                    # Check if the post ID is already in the seen IDs set.
                    if post.id in seen_ids:
                        continue

                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'selftext': post.selftext,
                        'url': post.url,
                        'subreddit': str(post.subreddit),
                        'score': post.score,
                        'upvote_ratio': post.upvote_ratio,
                    }

                    # Append the post data to the current posts list.
                    current_posts.append(post_data)
                    seen_ids.add(post.id)

                    # Acquire the rate limiter before making a request.
                    rate_limiter.acquire()
                    try:
                        # Scrape the comments from the post.
                        post.comments.replace_more(limit=50)
                    except prawcore.exceptions.RequestException as e:
                        print(f"Skipping comments for post {post.id} in r/{subreddit_name.strip()} due to error: {e}")
                        continue

                    for comment in post.comments.list():
                        if comment.id in seen_ids:
                            continue
                        comment_data = {
                            'id': comment.id,
                            'body': comment.body,
                            'author': str(comment.author),
                            'score': comment.score,
                        }
                        current_posts.append(comment_data)
                        seen_ids.add(comment.id)

                    # Check file size and save if necessary (~10MB).
                    if len(current_posts) >= post_limit:
                        file_size = save_posts(current_posts, file_index, output_dir, title, target_size_bytes)
                        total_size += file_size
                        print(f"Thread: saved {len(current_posts)} items to reddit_posts_{title}_{file_index}.json ({file_size / (1024 * 1024):.2f} MB)")
                        current_posts = []
                        file_index += 1

                        # Check if we should stop scraping.
                        with global_lock:
                            if stop_flag[0]:
                                print(f"Thread: stopping scraping for r/{subreddit_name.strip()} due to reaching target size.")
                                return total_size

                # If we reached the target size, break out of the loop.
                if total_size >= target_size_bytes:
                    break

        # If we had an invalid subreddit, we can skip to the next one.
        except prawcore.exceptions.RequestException as e:
            print(f"Error scraping {stream} posts from r/{subreddit_name.strip()}: {e}")
            continue

        # If we reached the target size, break out of the loop.
        if total_size >= target_size_bytes:
            break
        time.sleep(3) # Add a delay between streams to avoid overwhelming the server.

    # If there are any remaining posts, save them.
    if current_posts:
        file_size = save_posts(current_posts, file_index, output_dir, title, target_size_bytes)
        total_size += file_size
        print(f"Thread: saved {len(current_posts)} items to reddit_posts_{title}_{file_index}.json ({file_size / (1024 * 1024):.2f} MB)")
        file_index += 1

    return total_size

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
    seen_ids = load_existing_post_ids(output_dir)
    rate_limiter = RateLimiter(requests_per_min=60)  # Set the rate limit to 60 requests per minute.

    print(f"Scraping started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Validate subreddits.
    valid_subreddits = []
    for subreddit_name in subreddits:
        try:
            # Acquire the rate limiter before making a request.
            rate_limiter.acquire()
            # Attempt to access the subreddit.
            subreddit = reddit.subreddit(subreddit_name.strip())
            rate_limiter.acquire()
            # Check if the subreddit is valid and accessible.
            next(subreddit.hot(limit=1)) 
            valid_subreddits.append(subreddit_name.strip())
        except (prawcore.exceptions.NotFound, prawcore.exceptions.Forbidden, prawcore.exceptions.Redirect) as e:
            print(f"Pre-validation: Skipping invalid subreddit '{subreddit_name.strip()}': {e}")
        except prawcore.exceptions.RequestException as e:
            print(f"Error accessing subreddit '{subreddit_name.strip()}': {e}")
            continue

    # If no valid subreddits were found, exit the program.
    if not valid_subreddits:
        print("No valid subreddits found. Exiting.")
        return
    
    print(f"Found {len(valid_subreddits)} valid subreddits out of {len(subreddits)}.")
    subreddits = valid_subreddits

    # Split the subreddits into chunks for threading.
    num_threads = min(5, len(subreddits)) # Limit to 5 threads.
    subreddit_chunks = [subreddits[i::num_threads] for i in range(num_threads)]

    # Use ThreadPoolExecutor to scrape subreddits in parallel.
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i, chunk in enumerate(subreddit_chunks):
            for subreddit_name in chunk:
                futures.append(executor.submit(scrape_subreddit, subreddit_name, keywords, output_dir,
                                               target_size_bytes, seen_ids, rate_limiter))
                
        # Wait for all threads to complete and compute the total size.
        total_size = sum(f.result() for f in futures if f.result() is not None)

    # Print the total size of the scraped data.
    print(f"Total size of scraped data: {total_size / (1024 * 1024):.2f} MB")
    print(f"Scraping finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Global shared variables for tracking total size across threads.
global_size = [0]
global_lock = Lock()
stop_flag = [False] # Flag to stop threads if target size is reached.

if __name__ == "__main__":
    # Call our scrape_reddit function to start the scraping process.
    scrape_reddit()
