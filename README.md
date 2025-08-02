# ArXiv Paper Search Tool

Extract references from PDFs and search arXiv for similar papers, or search directly by arXiv ID.

## Installation

```bash
pip install PyMuPDF requests feedparser
sudo apt install mupdf  # PDF viewer
```

## Usage

**Three modes:**

1. **PDF reference extraction:**
   ```bash
   python srxiv.py <PDF_PATH> <REFERENCE_NUMBER> [<PATTERN_MODE>]
   ```

2. **PDF reference extraction from Supplementary Material:**
   ```bash
   python srxiv.py <PDF_PATH> S<REFERENCE_NUMBER> [<PATTERN_MODE>]
   ```

3. **Direct arXiv ID search:**
   ```bash
   python srxiv.py <ARXIV_ID>
   ```

**Examples:**
```bash
python srxiv.py paper.pdf 5          # Extract [5] from PDF
python srxiv.py paper.pdf S5         # Extract [5] of Supplementary Material from PDF
python srxiv.py paper.pdf 5 2        # Use pattern mode 2 for parsing
python srxiv.py 1234.56789           # Search by arXiv ID directly
```

## Pattern Modes

For reference parsing, you can specify pattern modes (1-3):
- **Mode 1**: Title in quotes: `[N] Authors, "Title", Journal (Year).`
- **Mode 2**: Title without quotes: `[N] Authors, Title, Journal (Year).`
- **Mode 3**: No title: `[N] Authors, Journal (Year).`

## Interactive Commands

- `m` - Show more results (5 at a time)
- `1`, `2`, `3`... - Download and open PDF (exits after opening)
- `q` - Quit

## How It Works

**PDF mode:**
1. Search PDF pages backwards to find reference page
2. Extract text from reference page and next page only
3. Parse reference using regex patterns to get authors and title
4. Search arXiv API using author names and title keywords

**arXiv ID mode:**
1. Directly fetch paper by arXiv ID from API
2. Display paper information

Downloaded PDFs: `{arxiv_id}_{title[:40]}.pdf`

