"""
ArXiv Paper Search Tool

Extract references from PDF and search for similar papers on arXiv based on author information
"""

import re
import sys
from typing import Optional, Tuple, List, Dict, Any
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
                print(f"Found reference: {line}")
                ref_block += re.sub(r"([.,])$", r"\1 ", line.rstrip("-"))

                # Continue reading until the next reference
                j = i + 1
                while (j < len(lines) and
                       not re.match(r"^\[\d+\]", lines[j])):
                    ref_block += re.sub(r"([.,])$",
                                        r"\1 ", lines[j].rstrip("-"))
                    j += 1
                break

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
        author_list = authors.split(", ")
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

        print(f"Found {len(feed.entries)} entries")

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
    def display_results(entries: List[ArxivEntry]) -> None:
        """Display search results"""
        for entry in entries:
            print(f"Similarity: {entry.similarity_score:.1f}")
            print(f"Title: {entry.title}")
            print(f"Authors: {', '.join(entry.authors)}")
            print(f"arXiv URL: {entry.arxiv_url}")
            print(f"PDF URL: {entry.pdf_url}")
            print("---")


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

        print(f"Authors: {authors}")
        print(f"Title: {title}")

        # arXiv search
        searcher = ArxivSearcher()
        results = searcher.search_by_authors(authors, title)

        # Display results
        displayer = ResultDisplayer()
        displayer.display_results(results)

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
