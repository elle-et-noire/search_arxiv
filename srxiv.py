import feedparser
import fitz
from rapidfuzz import fuzz
import re
import os
import requests
import subprocess
import sys


def get_reftxt(paper_path, refnum):
    with fitz.open(paper_path) as doc:
        paper_txt = "".join(page.get_text() for page in doc)

    lines = paper_txt.splitlines()
    try:
        start_idx = next(i for i, line in enumerate(
            lines) if line.startswith(f"[{refnum}]"))
    except StopIteration:
        return ""
    try:
        end_idx = next(i for i, line in enumerate(
            lines[start_idx+1:], start=start_idx+1) if re.match(r"^\[\d+\]", line))
    except StopIteration:
        end_idx = len(lines)

    reftxt = ""
    for j in range(start_idx, end_idx):
        if j + 1 < end_idx and not lines[j+1][0].isupper():
            reftxt += re.sub(r"([.,])$", r"\1 ", lines[j].rstrip("-"))
        else:
            reftxt += lines[j] + " "
    return reftxt.strip()


def request_arxiv(reftxt, max_results=100):
    id_match = re.search(r"arXiv:(?P<arxiv_id>[^\s,]+)", reftxt)
    if id_match:
        arxiv_id = id_match.group("arxiv_id")
        try:
            response = requests.get(
                f"https://export.arxiv.org/api/query", params={
                    "search_query": arxiv_id,
                    "start": 0,
                    "max_results": max_results
                }, timeout=10)
            print(response.url)
            response.raise_for_status()
            return feedparser.parse(response.text).entries
        except requests.RequestException as e:
            print(f"Error fetching arXiv ID {arxiv_id}: {e}")
            pass  # if request with arXiv ID fails, continue to search by authors

    match = re.compile(
        r"^(?:\[\d+\]\s)?(?P<authors>(?:.+? and .+?)|(?:[^,]+)),\s"
        r"(?P<title>.*),"
        r"(?P<source>[^,]+,[^,]+)$"
    ).match(reftxt)

    if not match:
        print("Match failed for the reference text:")
        print(reftxt)
        return

    title = match.group("title")
    authors = re.split(r",\s+|\s+and\s+",  match.group("authors"))
    query = []
    for author in authors:
        surname = author.split(" ")[-1]
        query.append(f"{surname}")

    if not query:
        print("No authors found in the reference text.")
        return

    try:
        response = requests.get(
            "https://export.arxiv.org/api/query", params={
                "search_query": ' '.join(query),
                "start": 0,
                "max_results": max_results
            }, timeout=10)
        print(response.url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching arXiv API: {e}")
        return

    feed = feedparser.parse(response.text)
    return sorted([e for e in feed.entries if fuzz.ratio(
        e.title, title) > 50], key=lambda e: fuzz.ratio(
        e.title, title), reverse=True)


def print_entry(e, j):
    print(f"[{j+1}]  {e.title}\n")
    print(f"  by {', '.join(author.name for author in e.authors)} ({e.id})\n")


def main():
    if len(sys.argv) < 3:
        print("Usage: python srxiv.py <PDF_PATH> <REFERENCE_NUMBER>")
        sys.exit(1)

    try:
        reftxt = get_reftxt(sys.argv[1], int(sys.argv[2]))
        if not reftxt:
            print("Failed to get reference text.")
            sys.exit(1)

    except (FileNotFoundError, ValueError) as e:
        print(f"Error processing input: {e}")
        sys.exit(1)

    entries = request_arxiv(reftxt)
    if not entries:
        return

    print()
    print_entry(entries[0], 0)

    disp_count = 1
    while True:
        try:
            s = "command (dl [1]st/[q]uit): " if len(
                entries) == 1 else f"command ([m]ore/dl [1-{len(entries)}]th/[q]uit): "
            user_input = input(s).strip().lower()

            if user_input == 'q':
                return
            if len(entries) > 1 and user_input == 'm':
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
            arxiv_id = e.id.split('/')[-1]
            title = "".join(
                c for c in e.title if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')[:40]
            filename = f"{arxiv_id}_{title}.pdf"

            if not os.path.exists(filename):
                try:
                    response = requests.get(
                        e.id.replace('/abs/', '/pdf/') + '.pdf', timeout=30)
                    response.raise_for_status()

                    if not response.content.startswith(b'%PDF'):
                        raise ValueError(
                            "Downloaded content is not a valid PDF")

                    with open(filename, 'wb') as f:
                        f.write(response.content)

                    print(f"Downloaded. ", end='')
                except requests.RequestException as e:
                    print(f"Download failed: {e}")
                    continue
                except ValueError as e:
                    print(f"Invalid file format: {e}")
                    continue
                except IOError as e:
                    print(f"File write error: {e}")
                    continue

            try:
                subprocess.run(['which', 'mupdf'],
                               check=True, capture_output=True)
                subprocess.Popen(['mupdf', filename],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                print(f"Opening {filename} ...")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("mupdf not found. Please install mupdf or open the file manually.")
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
