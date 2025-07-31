import feedparser
import fitz
from rapidfuzz import fuzz
import re
import os
import requests
import subprocess
import sys


def process_line(line):
    return re.sub(r"([.,])$", r"\1 ", line.rstrip("-"))


def get_reftxt(paper_path, refnum):
    reftxt = ""
    with fitz.open(paper_path) as doc:
        paper_txt = "".join(page.get_text() for page in doc)

    lines = paper_txt.splitlines()
    try:
        start_idx = next(i for i, line in enumerate(
            lines) if line.startswith(f"[{refnum}]"))
    except StopIteration:
        reftxt = ""
    else:
        try:
            end_idx = next(i for i, line in enumerate(
                lines[start_idx+1:], start=start_idx+1) if re.match(r"^\[\d+\]", line))
        except StopIteration:
            end_idx = len(lines)
        reftxt = "".join(map(process_line, lines[start_idx:end_idx])).strip()

    match = re.compile(
        r"^(?P<authors>(?:.+? and .+?)|(?:[^,]+)),\s"
        r"(?P<title>.*),\s"
        r"(?P<source>[^,]*,[^,]*)$"
    ).match(reftxt)

    return match.groupdict() if match else None


def request_arxiv(authors, max_results=100):
    blocks = re.split(r",\s+|\s+and+\s+", authors)
    query = []
    for author in blocks:
        surname = author.split(" ")[-1]
        if '-' not in surname:
            query.append(f'au:{surname}')

    try:
        response = requests.get(
            "https://export.arxiv.org/api/query", params={
                "search_query": " AND ".join(query),
                "start": 0,
                "max_results": max_results
            }, timeout=10)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        raise RuntimeError(f"arXiv API request failed: {e}")


def print_entry(e, j):
    print(f"[{j+1}]  {e.title}\n")
    print(f"  by {', '.join(author.name for author in e.authors)} ({e.id})\n")


def main():
    match = get_reftxt(sys.argv[1], int(sys.argv[2]))
    response = request_arxiv(match.get("authors", ""))
    if not response:
        print(f"No response with {response.url}")
        return
    feed = feedparser.parse(response.text)
    entries = sorted(feed.entries, key=lambda e: fuzz.ratio(
        e.title, match.get("title", "")), reverse=True)
    if not entries:
        print(f"No results with {response.url}")
        return

    print()
    print_entry(entries[0], 0)

    disp_count = 1
    while True:
        try:
            user_input = input(
                f"command ([m]ore/dl [1-{len(entries)}]th/[q]uit): ").strip().lower()
            if user_input == 'q':
                return
            if user_input == 'm':
                if disp_count >= len(entries):
                    print("No more entries.")
                    continue
                remaining = min(5, len(entries) - disp_count)
                for j in range(disp_count, disp_count + remaining):
                    print_entry(entries[j], j)
                disp_count += remaining
                continue
            if not user_input.isdigit() or not 0 < int(user_input) <= len(entries):
                print(f"Invalid input: {user_input}")
                continue
            e = entries[int(user_input) - 1]
            filename = f"{e.id.split('/')[-1]}_{"".join(c for c in e.title if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')[:40]}.pdf"

            if os.path.exists(filename):
                print(f"Opening existing {filename}...")
                subprocess.Popen(['mupdf', filename])
                return

            print(f"Downloading as {filename}")
            response = requests.get(e.id, timeout=30)
            response.raise_for_status()
            with open(filename, 'wb') as f:
                f.write(response.content)
            subprocess.Popen(['mupdf', filename])
            print(f"Opened {filename} with mupdf.")
            return

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Exiting...")
            break
        except EOFError:
            print("\n\nEOFError. Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue


if __name__ == "__main__":
    main()
