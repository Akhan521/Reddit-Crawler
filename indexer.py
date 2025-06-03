import os
import json
import lucene
from java.nio.file import Paths
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.document import Document, Field, TextField, StringField

# Initialize Lucene.
lucene.initVM()

# To index our Reddit JSON data, we will create a Lucene index.
def index_reddit_json(input_dir, index_dir):
    store = SimpleFSDirectory(Paths.get(index_dir))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    writer = IndexWriter(store, config)

    # Iterate through all JSON files in the input directory.
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(input_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        post = json.loads(line.strip())
                        doc = Document()
                        # Add fields to the document.
                        doc.add(StringField("id", post.get("id", ""), Field.Store.YES))
                        doc.add(StringField("author", post.get("author", "unknown"), Field.Store.YES))
                        doc.add(StringField("score", str(post.get("score", 0)), Field.Store.YES))
                        # Check if the post is a submission or a comment.
                        if 'title' in post:
                            doc.add(TextField("title", post.get("title", ""), Field.Store.YES))
                            doc.add(TextField("body", post.get("selftext", ""), Field.Store.YES))
                            doc.add(StringField("subreddit", post.get("subreddit", ""), Field.Store.YES))
                            doc.add(StringField("url", post.get("url", ""), Field.Store.YES))
                        # If it's a comment, we might have a different structure.
                        elif 'body' in post:
                            doc.add(TextField("body", post.get("body", ""), Field.Store.YES))
                        # Finally, we'll update our index with the document.
                        writer.addDocument(doc)
                    except Exception as e:
                        print(f"Error processing line in {filename}: {e}")

    writer.close()
    print("Indexing complete.")

if __name__ == "__main__":
    input_directory = "reddit_data"  # Our folder containing Reddit JSON files
    index_directory = "index"        # Output directory for the Lucene index.
    # Index the Reddit JSON files.
    index_reddit_json(input_directory, index_directory)
