# Deployment Instructions
To run our crawler.sh shell script, follow these steps:
1. Open a command prompt on your system.
2. If you haven’t, clone our repository onto your system.
3. Navigate to the folder with our code.
4. In praw.ini, put your Reddit username and password in our placeholders.
5. Type in the following commands:
```bash
chmod +x crawler.sh
./crawler.sh subreddits.txt keywords.txt reddit_data 500
```
6. Voila, that’s it!

Note: subreddits.txt is a list of subreddits to search through, keywords.txt is a list of keywords to filter for, reddit_data is our output directory where our scraped data is stored, and 500 indicates that we’d like to gather 500 MB of data.

# Customizations
1. If you wish to scrape from certain subreddits, navigate to the subreddits.txt file. Go ahead and specify the subreddits you wish to scrape ( line-separated ).
2. You may also filter for certain keywords by navigating to the keywords.txt file and specifying any keywords you'd like to consider here.
