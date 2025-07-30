import fitz
import sys
import re
import requests
import feedparser

def get_reftxt(paper_path, refnum):
  reftxt = "" 
  try:
    doc = fitz.open(paper_path)
    for page in doc:
      lines = page.get_text().splitlines()
      for i, line in enumerate(lines):
        if line.startswith(f"[{refnum}]"):
          reftxt += re.sub(r"([.,])$", r"\1 ", line.rstrip("-"))
          j = i + 1
          while j < len(lines) and not re.match(r"^\[\d+\]", lines[j]):
            reftxt += re.sub(r"([.,])$", r"\1 ", lines[j].rstrip("-"))
            j += 1
          break
    doc.close()
    return reftxt.strip()
  except Exception as e:
    raise RuntimeError(f"Failed to read PDF: {e}")

def request_arxiv(reftxt, author_num, max_results=10):
  blocks = re.split(r",\s+|\s+and+\s+", reftxt)
  query = []
  for author in blocks[:author_num]:
    surname = author.split(" ")[-1]
    if '-' not in surname:
      query.append(f'au:{surname}')

  params = {
    "search_query": " AND ".join(query),
    "start": 0,
    "max_results": max_results
  }

  try:
    response = requests.get("https://export.arxiv.org/api/query", params=params, timeout=10)
    response.raise_for_status()
    print(f"Request URL: {response.url}")
    return feedparser.parse(response.text)
  except requests.RequestException as e:
    raise RuntimeError(f"arXiv API request failed: {e}")


def main():
  reftxt = get_reftxt(sys.argv[1], int(sys.argv[2]))
  print(reftxt)
  request_arxiv(reftxt, int(sys.argv[3]))


if __name__ == "__main__":
    main()
