"""
ArXiv Paper Search Tool

Extract references from PDF and search for similar papers on arXiv based on author information
"""

import re
import sys
import os
import subprocess
from typing import Optional, Tuple, List, Any
from dataclasses import dataclass

import fitz
import requests
import feedparser
from rapidfuzz import fuzz


# Constants
ARXIV_API_BASE_URL = "https://export.arxiv.org/api/query"
DEFAULT_MAX_RESULTS = 10
CITATION_PATTERN = re.compile(
    r"^(?P<authors>(?:.+? and .+?)|(?:[^,]+)),\s"
    r"(?P<title>.*),\s"
    r"(?P<source>.*)$"
)


@dataclass
class ArxivEntry:
    """Data class for arXiv paper entry"""
    title: str
    authors: List[str]
    arxiv_url: str
    pdf_url: str
    similarity_score: float


class PDFProcessor:
    """Class responsible for PDF processing"""

    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """Extract text from PDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise RuntimeError(f"Failed to read PDF: {e}")


class CitationParser:
    """Class responsible for citation parsing"""

    @staticmethod
    def find_reference(text: str, ref_number: int) -> str:
        """Extract reference with the specified number"""
        lines = text.splitlines()
        ref_block = ""

        for i, line in enumerate(lines):
            if line.startswith(f"[{ref_number}]"):
                ref_block += re.sub(r"([.,])$", r"\1 ", line.rstrip("-"))

                # Continue reading until the next reference
                j = i + 1
                while (j < len(lines) and
                       not re.match(r"^\[\d+\]", lines[j])):
                    ref_block += re.sub(r"([.,])$",
                                        r"\1 ", lines[j].rstrip("-"))
                    j += 1
                break

        print(f"Ref: {ref_block.strip()}")
        return ref_block.strip()

    @staticmethod
    def extract_author_and_title(citation_string: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract author and title from citation string"""
        if not citation_string:
            return None, None

        match = CITATION_PATTERN.match(citation_string.strip())

        if match:
            authors = match.group("authors").strip()
            title = match.group("title").strip()
            return authors, title

        return None, None


class ArxivSearcher:
    """Class responsible for arXiv search"""

    def __init__(self, max_results: int = DEFAULT_MAX_RESULTS):
        self.max_results = max_results

    def _build_author_query(self, authors: str) -> str:
        """Build query from author names"""
        # Split by both ", " and " and "
        author_list = re.split(r",\s+|\s+and\s+", authors)
        # Remove empty strings and strip whitespace
        author_list = [author.strip()
                       for author in author_list if author.strip()]
        # Build query using only surnames
        query_parts = [f'au:{author.split(" ")[-1]}' for author in author_list]
        return " AND ".join(query_parts)

    def _make_request(self, query: str) -> feedparser.FeedParserDict:
        """Send request to arXiv API"""
        params = {
            "search_query": query,
            "start": 0,
            "max_results": self.max_results
        }

        try:
            response = requests.get(
                ARXIV_API_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            print(f"Request URL: {response.url}")
            return feedparser.parse(response.text)
        except requests.RequestException as e:
            raise RuntimeError(f"arXiv API request failed: {e}")

    def _calculate_similarity(self, target_title: str, entry_title: str) -> float:
        """Calculate similarity between titles"""
        return fuzz.ratio(target_title, entry_title)

    def _parse_entry(self, entry: Any, target_title: str) -> ArxivEntry:
        """Convert feed entry to ArxivEntry object"""
        authors = [author.name for author in entry.authors] if hasattr(
            entry, 'authors') else []
        arxiv_url = entry.id if hasattr(entry, 'id') else ""
        pdf_url = arxiv_url.replace(
            '/abs/', '/pdf/') + ".pdf" if arxiv_url else ""
        similarity = self._calculate_similarity(target_title, entry.title)

        return ArxivEntry(
            title=entry.title,
            authors=authors,
            arxiv_url=arxiv_url,
            pdf_url=pdf_url,
            similarity_score=similarity
        )

    def search_by_authors(self, authors: str, target_title: str) -> List[ArxivEntry]:
        """Search by author names and return results sorted by title similarity"""
        if not authors or not target_title:
            raise ValueError("Author names and title are required")

        query = self._build_author_query(authors)
        feed = self._make_request(query)

        # Parse entries and sort by similarity
        arxiv_entries = [
            self._parse_entry(entry, target_title)
            for entry in feed.entries
        ]

        # Sort by similarity score in descending order
        return sorted(arxiv_entries, key=lambda x: x.similarity_score, reverse=True)


class ResultDisplayer:
    """Class responsible for displaying results"""

    @staticmethod
    def open_pdf_with_viewer(filename: str) -> bool:
        """Open PDF with available viewer"""
        # Check if mupdf is available
        try:
            subprocess.run(['which', 'mupdf'], check=True, capture_output=True)
            print(f"Opening PDF with mupdf: {filename}")
            subprocess.Popen(['mupdf', filename],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            print("✓ PDF opened with mupdf")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠ mupdf not found. Trying alternative PDF viewers...")
            # Try alternative PDF viewers
            for viewer in ['evince', 'okular', 'xpdf', 'zathura']:
                try:
                    subprocess.run(['which', viewer],
                                   check=True, capture_output=True)
                    print(f"Opening PDF with {viewer}: {filename}")
                    subprocess.Popen([viewer, filename],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                    print(f"✓ PDF opened with {viewer}")
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

            print("⚠ No PDF viewer found. PDF file available but not opened.")
            return False

    @staticmethod
    def download_pdf_and_view(url: str, filename: str) -> bool:
        """Download PDF from URL and open with mupdf, or open existing file"""
        try:
            # Check if file already exists
            if os.path.exists(filename):
                print(f"✓ File already exists: {filename}")
                print("Opening existing PDF file...")
                return ResultDisplayer.open_pdf_with_viewer(filename)

            # Download the file if it doesn't exist
            print(f"Downloading PDF: {filename}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(filename, 'wb') as f:
                f.write(response.content)

            print(f"✓ Downloaded: {filename}")

            # Open the downloaded file
            return ResultDisplayer.open_pdf_with_viewer(filename)

        except Exception as e:
            print(f"✗ Failed to download PDF: {e}")
            return False

    @staticmethod
    def download_pdf(url: str, filename: str) -> bool:
        """Download PDF from URL (legacy method)"""
        try:
            print(f"Downloading PDF: {filename}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(filename, 'wb') as f:
                f.write(response.content)

            print(f"Downloaded: {filename}")
            return True
        except Exception as e:
            print(f"Failed to download PDF: {e}")
            return False

    @staticmethod
    def display_single_result(entry: ArxivEntry, index: int) -> None:
        """Display a single search result"""
        print(f"\n[{index}] (Similarity: {entry.similarity_score:.1f})")
        print("="*60)
        print(f"Title: {entry.title}")
        print(f"Authors: {', '.join(entry.authors)}")
        print(f"arXiv URL: {entry.arxiv_url}")
        print("="*60)

    @staticmethod
    def display_results_interactive(entries: List[ArxivEntry]) -> None:
        """Display search results interactively"""
        if not entries:
            print("No results found.")
            return

        # Display the first result (highest similarity)
        ResultDisplayer.display_single_result(entries[0], 1)

        displayed_count = 1

        while True:
            try:
                user_input = input("Enter command: ").strip().lower()

                if user_input == 'q':
                    print("Goodbye!")
                    break

                elif user_input == 'm':
                    # Show more results
                    if displayed_count < len(entries):
                        remaining = min(5, len(entries) - displayed_count)
                        print(f"\nShowing next {remaining} results:")
                        print("-"*40)

                        for i in range(displayed_count, displayed_count + remaining):
                            ResultDisplayer.display_single_result(
                                entries[i], i + 1)

                        displayed_count += remaining

                        if displayed_count >= len(entries):
                            print(f"✓ All {len(entries)} results displayed.")
                    else:
                        print("ℹ All results already displayed.")

                elif user_input.isdigit():
                    result_num = int(user_input)

                    if 1 <= result_num <= min(displayed_count, len(entries)):
                        entry = entries[result_num - 1]
                        # Generate safe filename from title and arXiv ID
                        arxiv_id = entry.arxiv_url.split(
                            '/')[-1] if entry.arxiv_url else "unknown"
                        safe_title = "".join(
                            c for c in entry.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_title = safe_title.replace(
                            ' ', '_')[:40]  # Limit length
                        filename = f"{arxiv_id}_{safe_title}.pdf"

                        print(f"\nDownloading result #{result_num}...")
                        success = ResultDisplayer.download_pdf_and_view(
                            entry.pdf_url, filename)
                        if success:
                            print(f"✓ Successfully saved as: {filename}")
                            print("Exiting interactive mode...")
                            break  # Exit the interactive loop
                        else:
                            print("✗ Download failed.")
                    else:
                        print(
                            f"✗ Invalid number. Please enter 1-{min(displayed_count, len(entries))}.")

                else:
                    print("✗ Invalid command. Please enter 'm', 'q', or a number.")

            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Exiting...")
                break
            except EOFError:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"✗ Error: {e}")
                continue


def main() -> None:
    """Main function"""
    if len(sys.argv) != 3:
        print("Usage: python search_arxiv.py <PDF_PATH> <REFERENCE_NUMBER>")
        sys.exit(1)

    try:
        pdf_path = sys.argv[1]
        ref_number = int(sys.argv[2])

        # PDF processing
        pdf_processor = PDFProcessor()
        text = pdf_processor.extract_text(pdf_path)

        # Citation parsing
        citation_parser = CitationParser()
        reference = citation_parser.find_reference(text, ref_number)
        authors, title = citation_parser.extract_author_and_title(reference)

        if not authors or not title:
            print("Failed to extract author names or title")
            sys.exit(1)

        # arXiv search
        searcher = ArxivSearcher()
        results = searcher.search_by_authors(authors, title)

        # Display results
        displayer = ResultDisplayer()
        displayer.display_results_interactive(results)

    except ValueError as e:
        print(f"Input error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
