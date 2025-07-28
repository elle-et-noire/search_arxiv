import re
import sys
import fitz
import requests
import feedparser
from rapidfuzz import fuzz


def pdf_to_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def find_ref(text, num):
    lines = text.splitlines()
    i = 0
    ref_block = ""
    while i < len(lines):
        if not lines[i].startswith(f"[{num}]"):
            i += 1
            continue
        print(lines[i])
        ref_block += re.sub(r"([.,])$", r"\1 ", lines[i].rstrip("-"))
        i += 1
        while i < len(lines) and not re.match(r"^\[\d+\]", lines[i]):
            ref_block += re.sub(r"([.,])$", r"\1 ", lines[i].rstrip("-"))
            i += 1

    return ref_block


def get_au_ti(citation_string):
    pattern = re.compile(
        r"^(?P<authors>(?:.+? and .+?)|(?:[^,]+)),\s"
        r"(?P<title>.*),\s"
        r"(?P<source>.*)$"
    )

    match = pattern.match(citation_string.strip())

    if match:
        authors = match.group("authors").strip()
        title = match.group("title").strip()
        return authors, title
    else:
        return None, None


def search_arxiv_by_authors(authors, title):
    split_authors = authors.split(", ")
    base_url = "https://export.arxiv.org/api/query"
    query = " AND ".join(
        [f'au:{author.split(" ")[-1]}' for author in split_authors])
    params = {
        "search_query": query,
        "start": 0,
        "max_results": 10
    }
    response = requests.get(base_url, params=params)
    print(response.url)
    feed = feedparser.parse(response.text)
    print(len(feed.entries))

    sorted_entries = sorted(feed.entries, key=lambda entry: fuzz.ratio(
        title, entry.title), reverse=True)

    for entry in sorted_entries:
        similarity = fuzz.ratio(title, entry.title)
        print(f"Similarity: {similarity:.1f}")
        print("Title:", entry.title)
        print("Authors:", ", ".join(author.name for author in entry.authors))
        print("arXiv URL:", entry.id)
        print("PDF URL:", entry.id.replace('/abs/', '/pdf/') + ".pdf")
        print("---")


if __name__ == "__main__":
    text = pdf_to_text(sys.argv[1])
    ref = find_ref(text, int(sys.argv[2]))
    authors, title = get_au_ti(ref)
    print("Authors:", authors)
    print("Title:", title)
    search_arxiv_by_authors(authors, title)
