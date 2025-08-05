"""ArXiv Paper Search Tool - Extract references from PDFs and search arXiv."""

import re
import argparse
import subprocess
import sys
from itertools import chain
import shutil
from pathlib import Path
import fitz
import feedparser
import requests


def get_reftxt(pdfpath, refnum: int, findnth=1):
    """Extract reference text from PDF by searching backwards for [refnum]."""
    with fitz.open(pdfpath) as doc:
        # Search pages backwards to find the page containing [refnum]
        count = 0
        pnum = -1
        for j in range(len(doc) - 1, -1, -1):
            if (refnum > 1 and re.search(rf"(^|\.\n)\[{refnum}\]", doc[j].get_text())) or \
               (refnum == 1 and re.search(rf"\n\[{refnum}\]", doc[j].get_text())):
                pnum = j
                count += 1
                if count >= findnth:
                    break

        if pnum == -1:
            return ""

        pdftxt = "".join(
            page.get_text() for page in doc[pnum:pnum + 2])

    lines = pdftxt.splitlines()
    try:
        ini = next(
            i for i, line in enumerate(lines)
            if line.startswith(f"[{refnum}]"))
    except StopIteration:
        return ""

    try:
        fin = next(
            i for i, line in enumerate(lines[ini+1:], start=ini+1)
            if re.match(r"^\[\d+\]", line))
    except StopIteration:
        fin = len(lines)

    reftxt = ""
    for j in range(ini, fin):
        # this procedure unevitably changes "non-unitary" to "nonunitary"
        if lines[j].endswith("-"):
            if j + 1 < fin and lines[j + 1][0].isupper():
                reftxt += lines[j]  # ex.) non-Hermitian
            else:
                reftxt += lines[j].rstrip("-")
        else:
            reftxt += lines[j] + " "

    return re.sub(r"^\[\d+\]", "", reftxt).strip()


def query_arxiv_api(query, max_results=10):
    """Query the arXiv API with given parameters."""
    req = requests.Request('GET', "https://export.arxiv.org/api/query", params={
        "search_query": query,
        "start": 0,
        "max_results": max_results,
    })
    prepared = req.prepare()
    print(prepared.url)
    with requests.Session() as s:
        response = s.send(prepared, timeout=10)
    response.raise_for_status()
    return feedparser.parse(response.text).entries


def request_arxiv(reftxt, mode=None, max_results=10):
    """Search arXiv API using reference text or arXiv ID."""
    id_match = re.search(r"ar-?Xiv:(?P<arxiv_id>[^\s,]+)", reftxt) or \
        re.search(r"(?P<arxiv_id>hep-th/\d{7,})", reftxt)

    if id_match:
        return query_arxiv_api(id_match.group("arxiv_id"), max_results)

    jnlpat = (r"((?:[^,]+,[^,]+\((?P<year1>\d+)\)\.)"
              r"|(?:[^,]+\((?P<year2>\d+)\)\s\d+\.))")

    refpat = [
        # case1: the title is surrounded by quotes
        re.compile(
            r"^(?P<authors>.*),\s"
            r"(“|\")(?P<title>.*),(”|\")\s"
            f"{jnlpat}"
        ),

        # case2: the title is not surrounded by quotes
        re.compile(
            r"^(?P<authors>(?:.+? and .+?)|(?:[^,]+)),\s"
            r"(?P<title>.*),\s"
            f"{jnlpat}"
        ),

        # case3: no title, just authors and journal
        re.compile(
            r"^(?P<authors>(?:.+? and .+?)|(?:[^,]+)),\s"
            f"{jnlpat}"
        )
    ]

    if mode is None or not 1 <= mode <= 3:
        match = refpat[0].match(reftxt) or refpat[1].match(
            reftxt) or refpat[2].match(reftxt)
    else:
        match = refpat[int(mode) - 1].match(reftxt)

    if not match:
        print("Match failed for the reference text:")
        print(reftxt)
        return None

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
        return None

    return query_arxiv_api(query, max_results)


def print_entry(e, j):
    """Print formatted arXiv entry with title and authors."""
    print(f"\n[{j+1}]  {e.title}\n")
    print(f"  by {', '.join(author.name for author in e.authors)} ({e.id})\n")


def dl_open_pdf(e):
    """Download PDF from arXiv entry and open with mupdf."""
    arxiv_id = e.id.split('/')[-1]
    safe_title = re.sub(r'[^\w\s-]', '', e.title)
    safe_title = re.sub(r'(\s|-)+', '_', safe_title).strip('_')[:40]
    filepath = Path(f"{arxiv_id}_{safe_title}.pdf")

    if not filepath.exists():
        with requests.get(
                e.id.replace('/abs/', '/pdf/') + '.pdf',
                timeout=30, stream=True) as response:
            response.raise_for_status()
            if not response.content.startswith(b'%PDF'):
                raise ValueError("Downloaded content is not a valid PDF.")
            filepath.write_bytes(response.content)
        print("Downloaded. ", end='')

    if mupdf_path := shutil.which('mupdf'):
        subprocess.Popen(
            [mupdf_path, filepath],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print(f"Opening {filepath.name} ...")
    else:
        print("mupdf not found. Please install mupdf or open the file manually.")


def interactive_search(entries):
    """Handle interactive search and download interface."""
    print_entry(entries[0], 0)

    dispnum = 1
    n = len(entries)
    while True:
        try:
            if n == 1:
                s = "command (dl [1]st/[q]uit): "
            else:
                s = f"command ([m]ore/dl [1-{n}]th/[q]uit): "

            c = input(s).strip().lower()

            if c == 'q':
                return

            if n > 1 and c == 'm':
                if dispnum >= n:
                    print("No more entries.")
                    continue
                remnum = min(5, n - dispnum)
                for j in range(dispnum, dispnum + remnum):
                    print_entry(entries[j], j)
                dispnum += remnum
                continue

            if not c.isdigit() or not 0 < int(c) <= len(entries):
                print(f"Invalid input: {c}")
                continue

            e = entries[int(c) - 1]
            dl_open_pdf(e)
            return  # Exit after opening PDF

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Exiting...")
            break
        except EOFError:
            print("\n\nEOFError. Exiting...")
            break


def main():
    """Main function - parse arguments and run interactive search."""
    parser = argparse.ArgumentParser(
        description="Search for arXiv papers from a PDF reference or an arXiv ID."
    )
    parser.add_argument(
        "id", help="Path to a PDF file or an arXiv ID.")
    parser.add_argument(
        "refnum", nargs='?', type=int,
        help="Reference number in the PDF (e.g., 23).")
    parser.add_argument(
        "-p", "--pattern", type=int, choices=[1, 2, 3],
        help="Force a specific regex pattern for reference parsing.")
    parser.add_argument(
        "-d", "--depth", type=int, default=1,
        help="Backwards search depth for the reference number.")
    parser.add_argument(
        "-i", "--inner-refnum", type=int, default=1,
        help="Specify n-th ref of multiple references.")

    args = parser.parse_args()

    if Path(args.id).is_file():
        if not args.refnum:
            print("Error: Reference number is required when providing a PDF file.")
            sys.exit(1)

        reftxt = get_reftxt(args.id, args.refnum, args.depth).split(";")[
            args.inner_refnum - 1].strip()
        if not reftxt:
            print("Failed to get reference text.")
            sys.exit(1)
    else:
        reftxt = f"arXiv:{args.id}"

    entries = request_arxiv(reftxt, mode=args.pattern)

    if not entries:
        sys.exit(1)

    interactive_search(entries)


if __name__ == "__main__":
    main()
