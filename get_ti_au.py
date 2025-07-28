import search_arxiv

if __name__ == "__main__":
    citations = {
        "Case 1 (3 Authors, arXiv)": "Y. Choi, B. C. Rayhaun, and Y. Zheng, Generalized Tube Algebras, Symmetry-Resolved Partition Functions, and Twisted Boundary States, arXiv:2409.02159",
        "Case 2 (2 Authors, Journal)": "T. Banks and E. Rabinovici, Finite Temperature Behavior of the Lattice Abelian Higgs Model, Nucl. Phys. B 160 (1979) 349–379",
        "Case 3 (1 Author, Journal+arXiv)": "Y. Tachikawa, On gauging finite subgroups, SciPost Phys. 8 (2020), no. 1 015, [arXiv:1712.09542]",
        "Case 4": "S. Hollands, GGI lectures on entropy, operator algebras and black holes, arXiv:2209.05132.",
        "Case 5": "L. D. Carlo, Monte Carlo, blocking, and inference: How to measure the renormalization group flow, arXiv:2401.04811",
        "Case 6": "G. Montambaux, Ramanujan, Landau and Casimir, divergent series: a physicist point of view, arXiv:2506.08664"
    }

    print("Running extraction for all provided citation formats...")

    for name, citation in citations.items():
        print("\n" + "="*45)
        print(f"--- {name} ---")
        authors, title = search_arxiv.get_au_ti(
            citation)
        if authors and title:
            print("✅ Extraction successful!")
            print(f"  Author(s): {authors}")
            print(f"  Title: {title}")
        else:
            print(f"❌ Extraction failed for string: {citation}")
    print("="*45)
