# ArXiv Paper Search Tool

Extract references from PDFs and search arXiv for similar papers, or search directly by arXiv ID.

## Installation

```bash
pip install PyMuPDF requests feedparser
sudo apt install mupdf  # Recommended PDF viewer
```

## Usage

```bash
python srxiv.py <id> [refnum] [-p PATTERN] [-d DEPTH] [-i INNER_REFNUM]
```

### Arguments

-   `id`: Path to a PDF file or an arXiv ID.
-   `refnum`: (Optional) The reference number to extract from the PDF. Required if `id` is a PDF file.
-   `-p, --pattern`: (Optional) Force a specific regex pattern (1-3) for parsing the reference.
-   `-d, --depth`: (Optional) Find the N-th occurrence of the reference when searching backwards from the end of the PDF. Default is 1.
-   `-i, --inner-refnum`: (Optional) If a reference block contains multiple citations separated by semicolons, specify which one to use (1-indexed). Default is 1.

### Modes of Operation

1.  **PDF Reference Extraction**: Provide a PDF path and a reference number.
    ```bash
    python srxiv.py path/to/paper.pdf 5
    ```
2.  **Direct arXiv ID Search**: Provide an arXiv ID.
    ```bash
    python srxiv.py 1234.56789
    ```

### Examples

```bash
# Extract reference [5] from a PDF
python srxiv.py paper.pdf 5

# Find the ref [5] in the main references when the PDF contains the references for Supplementary Material
python srxiv.py paper.pdf 5 --depth 2

# Extract the 2nd citation from a block like "[5] ...; ...; ..."
python srxiv.py paper.pdf 5 --inner-refnum 2

# Force parsing pattern #2 for a reference
python srxiv.py paper.pdf 5 --pattern 2

# Search directly by arXiv ID (new and old formats)
python srxiv.py 1234.56789
python srxiv.py hep-th/1234567
```

## Reference Parsing Patterns (`-p`)

-   **Pattern 1**: Title is surrounded by quotes.
    -   `Authors, "The Title," Journal...`
-   **Pattern 2**: Title is not surrounded by quotes.
    -   `Authors, The Title, Journal...`
-   **Pattern 3**: No title, only authors and journal info.
    -   `Authors, Journal...`

Patterns 2 and 3 assume that for multiple authors, the word "and" is used between the last two authors. However, this is not always the case. For a counterexample, see reference \[10\] in [hep-th/9802150](https://arxiv.org/abs/hep-th/9802150) (the `srxiv.py` works in this case because it can use the pattern 1).

## Interactive Commands

-   `m`: Show more results.
-   `1`, `2`, `3`...: Download and open the PDF for the selected entry.
-   `q`: Quit the application.

## How It Works

1.  **PDF Parsing**: If a PDF path is given, it searches backwards from the last page to find the page containing the specified reference number (`[N]`). It then extracts the text from that page and the next to ensure the full reference is captured.
2.  **Reference Matching**: It uses a set of regular expressions to parse the extracted text for authors and title. If the reference block contains multiple citations separated by semicolons (`;`), `--inner-refnum` can be used to select a specific one. A specific parsing pattern can be forced with the `--pattern` flag.
3.  **arXiv API Query**:
    -   If an `arXiv:ID` (including old formats like `hep-th/...`) is found in the reference, it queries the API directly with that ID.
    -   Otherwise, it constructs a search query using keywords from the parsed authors and title.
4.  **Results**: Displays the search results and enters an interactive mode for browsing and downloading.

Downloaded PDFs are saved as `{arxiv_id}_{safe_title}.pdf`.

