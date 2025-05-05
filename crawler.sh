#!/bin/bash
# A shell script for our python reddit crawler.

# Check for our required arguments.
if [ $# -ne 4 ]; then
    echo "Usage: $0 <subreddits-file> <keywords-file> <output_dir> <target_size_mb>"
    exit 1
fi

# Assign arguments to variables.
SUBREDDITS_FILE=$1
KEYWORDS_FILE=$2
OUTPUT_DIR=$3
TARGET_SIZE_MB=$4

# Create the output directory if it doesn't exist.
mkdir -p "$OUTPUT_DIR"
# Check if the output directory was created successfully.
if [ $? -ne 0 ]; then
    echo "Error: Could not create output directory $OUTPUT_DIR"
    exit 1
fi

# Run the Python script with the provided arguments.
python3 reddit_crawler.py "$SUBREDDITS_FILE" "$KEYWORDS_FILE" "$OUTPUT_DIR" "$TARGET_SIZE_MB"

# Output a message indicating the script has finished.
echo "Crawling completed. Data saved to $OUTPUT_DIR."
