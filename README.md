# 🕷️ Reddit Crawler & Search App

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

- **Python**: Reddit crawling, data preprocessing, and Flask web server
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

## 🖥️ Demo

https://github.com/user-attachments/assets/98df88a3-2e69-4b7f-9e23-d682d4c1b21b

---

## 🔎 What We Learned

### Technical Lessons
- How to **scrape large datasets** using PRAW and parallel threads with rate limiting
- Using **Lucene** via PyLucene to build fast, custom search engines
- Parsing external pages to enrich data using **BeautifulSoup**
- Clean data processing and storage techniques (deduplication, chunking)
- Building a Flask app that integrates with a search backend

### Collaboration & Design
- Designing around **modularity** (each script has a single responsibility)
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
```

---

## 🛠️ Getting Started

Follow the steps below to run the project on your machine.

### 🕸️ Note: Crawling-Only Users

If you **only want to crawl Reddit data** and are **not interested in searching through it using our web app**, you can **skip all steps involving PyLucene setup** and the **Flask search interface**.

In other words:
- You **do not need PyLucene** if you're only crawling.
- You **do not need to run** the indexing script (`indexer.py`) or the web app (`search_app.py`).
- Just follow the instructions to run `crawler.sh` with the provided arguments (see steps 0-3).

This makes the project easier to use for data gathering without requiring any Java or Lucene installation.

### ✅ Prerequisites

Ensure the following are installed:

- **Python 3.8+**
- **Java 11+**
- **[PyLucene](https://dlcdn.apache.org/lucene/pylucene/)**: for info on how to install and configure PyLucene, [click here](https://lucene.apache.org/pylucene/install.html).
- Python libraries:
  - `praw`
  - `flask`
  - `bs4`
  - `pandas`
  - `requests`

0. Install Python Libraries Using:

   ```bash
   pip install praw flask beautifulsoup4 pandas requests
   ```

1. Clone The Repository
   ```bash
   git clone https://github.com/Akhan521/Reddit-Crawler.git
   cd Reddit-Crawler
   ```
2. Prepare Input Files
   
   Make sure the following input files exist:

   - subreddits.txt: each line contains a subreddit name (e.g. technology)
   - keywords.txt: each line contains a keyword to filter Reddit posts
  
   You should also create an empty folder where scraped data will be saved:
   ```bash
   mkdir reddit_data
   ```

4. Run The Reddit Crawler
   
   Use the provided shell script:
   ```bash
   /crawler.sh subreddits.txt keywords.txt reddit_data 30
   ```
   > Note: The last argument is the size (in MB) of data you want to collect (e.g. 30 MB of data).
   
   This will:
     - Scrape Reddit posts/comments across hot, top, new, and rising
     - Save ~10MB JSON chunks to the reddit_data folder
     - Enrich posts by extracting titles from linked pages
     - Stop once it collects at least 30MB of data (adjustable)
  
5. Index the Data with PyLucene
   
   Once data is collected, index it using:
   ```bash
   python3 indexer.py
   ```

   This script:
     - Reads all .json files from the reddit_data/ folder
     - Builds a Lucene index for our search engine
     - Indexes fields like title, body, author, subreddit, and score
  
7. Launch the Search App
   
   To start the web UI:
   ```bash
   python3 search_app.py
   ```

   Then open your browser and go to:
   ```bash
   http://localhost:5000
   ```

   You can now:
     - Type search queries into the interface
     - Get the top 10 Reddit matches with title, author, and body
     - Click “Back to Search” to run another query
  
9. (Optional) Customize Your Crawl
   - Add more subreddits to subreddits.txt
   - Add new filters to keywords.txt
   - Increase or decrease target scrape size by modifying the last argument (e.g., 30 = 30MB)
  
---

## 💡 Reflections

This project taught us how to build a working IR system, including crawling, parsing, indexing, and querying real-world Reddit data. We:
  - Gained hands-on experience with multi-threaded scraping and API rate limiting
  - Learned how to use Apache Lucene via PyLucene for indexing and searching large corpora
  - Built a lightweight search app to visualize results of scraping
  - Applied error handling and clean code structure for scalability and modularity

Most importantly, we deepened our understanding of information retrieval, and how data pipelines can power real-time search over unstructured content.

---

## 👤 Authors

**Aamir Khan**: [GitHub](https://github.com/Akhan521) || **Ihsan Sarwar**: [GitHub](https://github.com/IhsanSarwar) || **Jyro Jimenez**: [GitHub](https://github.com/jyroball) || **Jonathan Jin**: [GitHub](https://github.com/jjin1407)

---

## Support Us!

If you found this project interesting, feel free to ⭐ the repository! Thank you for your time and reading about our project.

We’d love to hear your feedback, questions, and ideas, so reach out anytime.
   
