import requests
import feedparser
import pdf_to_text
import get_ti_au
import sys
from rapidfuzz import fuzz

def search_arxiv_by_authors(authors):
    split_authors = authors.split(", ")
    base_url = "https://export.arxiv.org/api/query"
    query = " AND ".join([f'au:{author.split(" ")[-1]}' for author in split_authors])
    params = {
        "search_query": query,
        "start": 0,
        "max_results": 10
    }
    response = requests.get(base_url, params=params)
    print(response.url)
    feed = feedparser.parse(response.text)
    print(len(feed.entries))
    for entry in feed.entries:
        print("Title:", entry.title)
        print("Authors:", ", ".join(author.name for author in entry.authors))
        print("arXiv URL:", entry.id)
        print("PDF URL:", entry.id.replace('/abs/', '/pdf/') + ".pdf")
        print("---")

if __name__ == "__main__":
    text = pdf_to_text.pdf_to_text(sys.argv[1])
    ref = pdf_to_text.find_ref(text, int(sys.argv[2]))
    authors, title = get_ti_au.extract_author_and_title_universal(ref)
    print("Authors:", authors)
    print("Title:", title)
    search_arxiv_by_authors(authors)
