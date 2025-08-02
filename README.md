# ArXiv Paper Search Tool

Extract references from PDFs and search arXiv for similar papers using fuzzy title matching, or search directly by arXiv ID.

## Installation

```bash
pip install PyMuPDF requests feedparser rapidfuzz
sudo apt install mupdf  # PDF viewer
```

## Usage

**Two modes:**

1. **PDF reference extraction:**
   ```bash
   python srxiv.py <PDF_PATH> <REFERENCE_NUMBER>
   ```

2. **Direct arXiv ID search:**
   ```bash
   python srxiv.py <ARXIV_ID>
   ```

**Examples:**
```bash
python srxiv.py paper.pdf 5          # Extract reference [5] from PDF
python srxiv.py 1234.56789           # Search by arXiv ID directly
```

## Interactive Commands

- `m` - Show more results (5 at a time)
- `1`, `2`, `3`... - Download and open PDF (exits after opening)
- `q` - Quit

## How It Works

**PDF mode:**
1. Extract text from PDF using PyMuPDF
2. Parse reference `[N]` to get authors and title
3. Search arXiv API using author surnames
4. Rank results by fuzzy title matching (threshold: 50%)

**arXiv ID mode:**
1. Directly fetch paper by arXiv ID
2. Display paper information

Downloaded PDFs: `{arxiv_id}_{title}.pdf`


