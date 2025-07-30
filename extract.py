import re


def extract_author_and_title_universal(citation_string):
    """
    Extracts the author(s) and title from various citation string formats.
    This version handles single/multiple authors and titles containing commas.

    Args:
      citation_string: The citation string.

    Returns:
      A tuple of (authors, title), or (None, None) if extraction fails.
    """
    # This pattern is robust enough for the new case because `(?P<title>.*)`
    # greedily matches everything, including commas, until the final
    # comma that separates the title from the source.
    pattern = re.compile(
        r"^(?P<authors>(?:.+? and .+?)|(?:[^,]+)),\s"  # Authors (1 or more)
        # Title (handles internal commas)
        r"(?P<title>.*),\s"
        r"(?P<source>.*)$"                             # Source
    )

    match = pattern.match(citation_string.strip())

    if match:
        authors = match.group("authors").strip()
        title = match.group("title").strip()
        return authors, title
    else:
        return None, None


# --- Testing All Formats ---
citations = {
    "Case 1 (3 Authors)": "Y. Choi, B. C. Rayhaun, and Y. Zheng, Generalized Tube Algebras, Symmetry-Resolved Partition Functions, and Twisted Boundary States, arXiv:2409.02159",
    "Case 2 (2 Authors)": "T. Banks and E. Rabinovici, Finite Temperature Behavior of the Lattice Abelian Higgs Model, Nucl. Phys. B 160 (1979) 349–379",
    "Case 3 (1 Author)": "Y. Tachikawa, On gauging finite subgroups, SciPost Phys. 8 (2020), no. 1 015, [arXiv:1712.09542]",
    "Case 4 (Title w/ Commas)": "K. Minami, Infinite number of solvable generalizations of xy-chain, with cluster state, and with central charge c=m/2, Nucl. Phys. B 925, 144 (2017)."
}

print("✅ Running extraction for all citation formats...")

for name, citation in citations.items():
    print("\n" + "="*45)
    print(f"--- {name} ---")
    authors, title = extract_author_and_title_universal(citation)
    if authors and title:
        print("Extraction successful!")
        print(f"  Author(s): {authors}")
        print(f"  Title: {title}")
    else:
        print(f"❌ Extraction failed for string: {citation}")
print("="*45)
