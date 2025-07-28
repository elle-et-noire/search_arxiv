# ArXiv Paper Search Tool

A powerful Python tool that extracts references from PDF files and searches for similar papers on arXiv based on author information and title similarity.

## Features

- 📄 **PDF Text Extraction**: Extract text content from PDF files using PyMuPDF
- 🔍 **Reference Parsing**: Automatically locate and parse numbered references from academic papers
- 🎯 **Author & Title Extraction**: Extract author names and paper titles from citation strings
- 🔗 **ArXiv API Integration**: Search arXiv database using author surnames
- 📊 **Similarity Ranking**: Rank search results by title similarity using fuzzy string matching
- 💻 **Interactive Interface**: User-friendly command-line interface with progressive result display
- 📱 **PDF Download & Viewing**: Automatically download and open PDFs with mupdf or alternative viewers
- 🔄 **Flexible Author Parsing**: Handle both comma-separated and "and"-separated author lists

## Installation

### Prerequisites

- Python 3.7+
- PDF viewer (mupdf recommended, with fallback to evince, okular, xpdf, or zathura)

### Required Python Packages

Install the required dependencies:

```bash
pip install PyMuPDF requests feedparser rapidfuzz
```

Or install from requirements file:

```bash
pip install -r requirements.txt
```

### System Dependencies

Install a PDF viewer (recommended: mupdf):

**Ubuntu/Debian:**
```bash
sudo apt-get install mupdf
```

**Fedora/RHEL:**
```bash
sudo dnf install mupdf
```

**macOS:**
```bash
brew install mupdf
```

## Usage

### Basic Usage

```bash
python search_arxiv.py <PDF_PATH> <REFERENCE_NUMBER>
```

### Parameters

- `PDF_PATH`: Path to the PDF file containing references
- `REFERENCE_NUMBER`: The number of the reference to search for (e.g., 1, 2, 3...)

### Example

```bash
python search_arxiv.py paper.pdf 5
```

This will:
1. Extract text from `paper.pdf`
2. Find reference number [5]
3. Parse author names and title
4. Search arXiv for similar papers
5. Display results ranked by similarity

### Interactive Commands

Once results are displayed, you can use these commands:

- `m` - Show more results (displays 5 additional results)
- `1`, `2`, `3`... - Download PDF of the specified result number
- `q` - Quit the application

When you download a PDF, the tool will:
- Download the paper to your current directory
- Automatically open it with mupdf (or available PDF viewer)
- Exit the interactive mode

## How It Works

### 1. PDF Processing
The tool uses PyMuPDF to extract text content from PDF files, handling various PDF formats and layouts.

### 2. Reference Extraction
It searches for numbered references in the format `[N]` where N is the reference number, then extracts the complete citation text until the next reference.

### 3. Citation Parsing
Using regular expressions, it parses citation strings to extract:
- Author names (supporting both "Smith, J. and Doe, A." and "Smith, J., Doe, A." formats)
- Paper title
- Publication details

### 4. ArXiv Search
The tool constructs search queries using author surnames and queries the arXiv API to find potentially matching papers.

### 5. Similarity Ranking
Results are ranked using fuzzy string matching (Levenshtein distance) between the extracted title and arXiv paper titles.

### 6. Interactive Display
Results are presented progressively, starting with the highest similarity match, allowing users to explore results efficiently.

## File Naming Convention

Downloaded PDFs are saved with the format:
```
{arxiv_id}_{safe_title}.pdf
```

For example: `2301.12345_Deep_Learning_for_Natural_Language.pdf`

## Supported Citation Formats

The tool can parse various citation formats including:

```
Smith, J. and Doe, A., "Paper Title", Journal Name, 2023.
Smith, J., Doe, A., "Paper Title", Conference Proceedings, 2023.
Smith, J., Doe, A. and Wilson, B., "Paper Title", arXiv preprint, 2023.
```

## Error Handling

The tool includes comprehensive error handling for:
- Invalid PDF files
- Network connectivity issues
- Missing references
- Citation parsing failures
- PDF viewer availability

## Dependencies

### Python Packages
- `PyMuPDF` (fitz) - PDF text extraction
- `requests` - HTTP requests to arXiv API
- `feedparser` - Parsing arXiv API responses
- `rapidfuzz` - Fuzzy string matching for similarity scoring

### System Requirements
- Python 3.7 or higher
- Internet connection for arXiv API access
- PDF viewer for automatic document opening

## Limitations

- Only works with numbered references in `[N]` format
- Requires internet connection for arXiv searches
- Citation parsing may fail with non-standard formats
- Limited to papers available on arXiv

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Author

Created by [elle-et-noire](https://github.com/elle-et-noire)

## Acknowledgments

- arXiv for providing the open access repository and API
- PyMuPDF team for the excellent PDF processing library
- rapidfuzz developers for fast string matching algorithms
