# ArXiv Paper Search Tool

Extract references from PDFs and search arXiv for similar papers using fuzzy title matching.

## Installation

```bash
pip install PyMuPDF requests feedparser rapidfuzz
sudo apt install mupdf  # PDF viewer
```

## Usage

```bash
python srxiv.py <PDF_PATH> <REFERENCE_NUMBER>
```

**Example:**
```bash
python srxiv.py paper.pdf 5
```

This extracts reference [5] from `paper.pdf`, searches arXiv by author names, and displays results sorted by title similarity (threshold: 50%).

## Interactive Commands

- `m` - Show more results (5 at a time)
- `1`, `2`, `3`... - Download and open PDF
- `q` - Quit

## How It Works

1. Extract text from PDF using PyMuPDF
2. Parse reference `[N]` to get authors and title
3. Search arXiv API using author surnames
4. Rank results by fuzzy title matching
5. Filter results with similarity > 50%

Downloaded PDFs: `{arxiv_id}_{title}.pdf`

