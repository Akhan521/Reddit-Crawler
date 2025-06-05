from flask import Flask, render_template, request
import lucene
from java.nio.file import Paths
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.analysis.standard import StandardAnalyzer

app = Flask(__name__, template_folder='templates')

# Initialize JVM for Lucene
vm_env = lucene.initVM()

# Set index directory path
INDEX_DIR = 'index'
directory = FSDirectory.open(Paths.get(INDEX_DIR))
searcher = IndexSearcher(DirectoryReader.open(directory))
analyzer = StandardAnalyzer()

@app.route('/', methods=['GET'])
def search_form():
    return render_template('search.html')

@app.route('/results', methods=['POST'])
def search_results():
    vm_env.attachCurrentThread()
    query_str = request.form['query']
    parser = QueryParser("body", analyzer)  # Search within 'body' field
    query = parser.parse(query_str)
    hits = searcher.search(query, 10).scoreDocs

    results = []
    for hit in hits:
        doc = searcher.doc(hit.doc)
        result = {
            'score': hit.score,
            'title': doc.get("title"),
            'body': doc.get("body"),
            'username': doc.get("author")
        }
        results.append(result)

    return render_template('results.html', query=query_str, results=results)

if __name__ == '__main__':
    app.run(debug=True)
