# 🔎 Reddit Crawler & Search App

**An end-to-end Reddit crawler and search engine** that scrapes Reddit posts, filters them by keywords, enriches with external page titles, and enables full-text search using PyLucene, all wrapped in a minimal, searchable web app.

---

## 📌 What is This Project?

This project combines **web crawling**, **natural language data collection**, **indexing**, and **information retrieval** into one cohesive pipeline.

It allows you to:
- Crawl Reddit posts and comments across multiple subreddits
- Filter by keywords and target a data collection size (in MB)
- Save enriched Reddit data (with linked page titles) into JSON
- Index this data using **Apache Lucene** (Information Retrieval Technique)
- Search the indexed content through a **web interface (Flask)**

---

## 💡 Why We Built It

We wanted to build a lightweight Reddit crawler and search engine from scratch. We were curious about:
- How to collect and clean Reddit data in bulk
- How to build an efficient search index using classical IR techniques (Lucene)
- How to present results in a minimal and simple usable interface

---

## ⚙️ Tech Stack

- **Python 3**: Reddit crawling, data preprocessing, and Flask web server
- **PRAW**: Python Reddit API Wrapper
- **ThreadPoolExecutor**: Parallel subreddit crawling
- **Apache Lucene + PyLucene**: Powerful full-text indexing and search
- **Flask**: Web app to search and display results
- **HTML/Jinja**: Search + results templates

---

## 🧠 Key Features

| Feature                       | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| Multi-threaded Crawling    | Efficiently scrape multiple subreddits in parallel                         |
| Keyword Filtering          | Only save posts and comments that match your keyword list                  |
| Linked Page Titles         | Automatically extract page titles for any external links inside posts      |
| Robust Error Handling      | Handles invalid subreddits, rate limits, and duplicates                    |
| JSON Output                | Saves data in clean newline-delimited JSON (~10MB per file)                |
| Full-Text Search Engine    | Index Reddit content using PyLucene for lightning-fast querying            |
| Simple Web App             | Enter a search query and browse matching Reddit posts/comments             |

---

## 🔎 What We Learned

### Technical Lessons
- How to **scrape large datasets** using PRAW and parallel threads with rate limiting
- Using **Lucene** via PyLucene to build fast, custom search engines
- Parsing external pages to enrich data using **BeautifulSoup**
- Clean data processing and storage techniques (deduplication, chunking)
- Building a Flask app that integrates with a search backend

### Collaboration & Design
- Designing around **modularity** — each script has a single responsibility
- Coordinating shared global states and safe multi-threading with locks
- Handling I/O errors and edge cases in real-world data
- Writing tools that are easy for others to use (via bash scripts + argument parsing)

---

## 📁 Project Structure

```bash
Reddit-Search-App/
├── reddit_crawler.py         # Reddit scraping logic
├── indexer.py                # Indexes Reddit JSON files with Lucene
├── search_app.py             # Flask web app for search interface
├── crawler.sh                # Shell script to run the crawler
├── templates/
│   ├── search.html           # Search form
│   └── results.html          # Display search results
├── sample_data.json          # Example Reddit data
├── subreddits.txt            # List of subreddits to crawl
├── keywords.txt              # List of filter keywords
├── .gitignore
└── README.md
