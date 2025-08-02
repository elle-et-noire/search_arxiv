import feedparser
import fitz
import re
import os
import requests
import subprocess
import sys
from itertools import chain


def get_reftxt(pdfpath, refnum, findnth=2):
    with fitz.open(pdfpath) as doc:
        # Search pages backwards to find the page containing [refnum]
        count = 0
        refpagenum = None
        for pagenum in range(len(doc) - 1, -1, -1):
            pagetxt = doc[pagenum].get_text()
            if re.search(rf"(^|\.\n)\[{refnum}\]", pagetxt):
                refpagenum = pagenum
                count += 1
                if count >= findnth:
                    break

        if refpagenum is None:
            return ""

        # Only use text up to the page containing the reference
        pdftxt = "".join(page.get_text()
                         for page in doc[refpagenum:refpagenum + 2])

    lines = pdftxt.splitlines()
    ini = 0
    while ini < len(lines):
        # deal with cases where the reference number accidentally appears at the head of a line in the main text
        if lines[ini].startswith(f"[{refnum}]") and ini > 0 and lines[ini-1].strip().endswith("."):
            break
        ini += 1
    try:
        fin = next(i for i, line in enumerate(
            lines[ini+1:], start=ini+1) if re.match(r"^\[\d+\]", line))
    except StopIteration:
        fin = len(lines)

    reftxt = ""
    for j in range(ini, fin):
        # this procedure cannot deal with for example "non-unitary"
        if lines[j].endswith("-"):
            if j + 1 < fin and lines[j + 1][0].isupper():
                reftxt += lines[j]  # ex.) non-Hermitian
            else:
                reftxt += lines[j].rstrip("-")
        else:
            reftxt += lines[j] + " "
    return reftxt.strip()


def request_arxiv(reftxt, mode=None, max_results=10):
    id_match = re.search(r"ar\s?Xiv:(?P<arxiv_id>[^\s,]+)", reftxt)
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
            print(f"Error in fetching with arXiv ID {arxiv_id}: {e}")
            sys.exit(1)

    refpat = [
        # case1: the title is surrounded by quotes
        re.compile(
            r"^\[\d+\]\s(?P<authors>.*),\s"
            r"(“|\")(?P<title>.*),(”|\")\s"
            r"(?:[^,]+,[^,]+\((?P<year1>\d+)\)\.)|(?:[^,]+\((?P<year2>\d+)\)\s\d+\.)"
        ),

        # case2: the title is not surrounded by quotes
        re.compile(
            r"^\[\d+\]\s(?P<authors>(?:.+? and .+?)|(?:[^,]+)),\s"
            r"(?P<title>.*),\s"
            r"(?:[^,]+,[^,]+\((?P<year1>\d+)\)\.)|(?:[^,]+\((?P<year2>\d+)\)\s\d+\.)"
        ),

        # case3: no title, just authors and journal
        re.compile(
            r"^\[\d+\]\s(?P<authors>(?:.+? and .+?)|(?:[^,]+)),\s"
            r"(?:[^,]+,[^,]+\((?P<year1>\d+)\)\.)|(?:[^,]+\((?P<year2>\d+)\)\s\d+\.)"
        )
    ]

    if mode is None or not mode.isdigit() or not 1 <= int(mode) <= 3:
        match = refpat[0].match(reftxt) or refpat[1].match(
            reftxt) or refpat[2].match(reftxt)
    else:
        match = refpat[int(mode) - 1].match(reftxt)

    if not match:
        print("Match failed for the reference text:")
        print(reftxt)
        sys.exit(1)

    title = match.group("title").strip(
    ) if "title" in match.groupdict() else ""
    authors = match.group("authors").strip()
    # single alphabet is noisy for search
    word_pattern = r'\b(?![Aa]nd\b)[a-zA-Z0-9]{2,}\b'
    query = ' '.join(chain(
        (f'au:{w}' for w in sorted(re.findall(
            word_pattern, authors), key=len, reverse=True)),
        re.findall(word_pattern, title)
    ))

    if not query:
        print("No authors and title words in the reference text:")
        print(reftxt)
        sys.exit(1)

    try:
        response = requests.get(
            "https://export.arxiv.org/api/query", params={
                "search_query": query,
                "start": 0,
                "max_results": max_results
            }, timeout=10)
        print(response.url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching arXiv API: {e}")
        sys.exit(1)

    return feedparser.parse(response.text).entries


def print_entry(e, j):
    print(f"[{j+1}]  {e.title}\n")
    print(f"  by {', '.join(author.name for author in e.authors)} ({e.id})\n")


def dl_open_pdf(e):
    arxiv_id = e.id.split('/')[-1]
    title = "".join(c for c in e.title if c.isalnum() or c in (
        ' ', '-', '_'))[:40].rstrip().replace(' ', '_')
    filename = f"{arxiv_id}_{title}.pdf"

    if not os.path.exists(filename):
        response = requests.get(
            e.id.replace('/abs/', '/pdf/') + '.pdf', timeout=30)
        response.raise_for_status()
        if not response.content.startswith(b'%PDF'):
            raise ValueError("Downloaded content is not a valid PDF.")

        with open(filename, 'wb') as f:
            f.write(response.content)

        print(f"Downloaded. ", end='')

    try:
        subprocess.run(['which', 'mupdf'], check=True, capture_output=True)
        subprocess.Popen(['mupdf', filename],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        print(f"Opening {filename} ...")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("mupdf not found. Please install mupdf or open the file manually.")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python srxiv.py <PDF_PATH> <REFERENCE_NUMBER> [<REFERENCE_PATTERN>] |\n       python srxiv.py <arXiv_ID>")
        sys.exit(1)

    if os.path.isfile(sys.argv[1]):
        try:
            if sys.argv[2].isdigit():
                reftxt = get_reftxt(sys.argv[1], int(sys.argv[2]))
            else:
                reftxt = get_reftxt(sys.argv[1], int(sys.argv[2][1:]), 1)

            if not reftxt:
                print("Failed to get reference text.")
                sys.exit(1)

        except (FileNotFoundError, ValueError) as e:
            print(f"Error processing input: {e}")
            sys.exit(1)
    else:
        reftxt = "arXiv:" + sys.argv[1]

    entries = request_arxiv(
        reftxt, mode=sys.argv[3] if len(sys.argv) > 3 else None)
    if not entries:
        sys.exit(1)

    print()
    print_entry(entries[0], 0)

    disp_count = 1
    while True:
        try:
            if (n := len(entries)) == 1:
                s = "command (dl [1]st/[q]uit): "
            else:
                s = f"command ([m]ore/dl [1-{n}]th/[q]uit): "

            user_input = input(s).strip().lower()

            if user_input == 'q':
                return
            if len(entries) > 1 and user_input == 'm':
                if disp_count >= len(entries):
                    print("No more entries.")
                    continue
                remnum = min(5, len(entries) - disp_count)
                for j in range(disp_count, disp_count + remnum):
                    print_entry(entries[j], j)
                disp_count += remnum
                continue
            if not user_input.isdigit() or not 0 < int(user_input) <= len(entries):
                print(f"Invalid input: {user_input}")
                continue

            e = entries[int(user_input) - 1]
            dl_open_pdf(e)
            break

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Exiting...")
            break
        except EOFError:
            print("\n\nEOFError. Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
