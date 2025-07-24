import requests
import feedparser
import pdf_to_text

def search_arxiv_by_title(title):
    base_url = "https://export.arxiv.org/api/query"
    # query = f'ti:{title} AND au:ryu AND au:chang AND au:you AND au:wen'
    # query = "au:ryu AND au:chang AND au:you AND au:wen AND cat:physics"
    query = "au:pylyavskyy AND au:skopenkov"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": 10
    }
    response = requests.get(base_url, params=params)
    print(response.url)
    feed = feedparser.parse(response.text)
    print(len(feed.entries))
    for entry in feed.entries:
        print("Title:", entry.title)
        print("Authors:", ", ".join(author.name for author in entry.authors))
        print("arXiv URL:", entry.id)
        print("PDF URL:", entry.id.replace('/abs/', '/pdf/') + ".pdf")
        print("---")

# search_arxiv_by_title("Tensor network simulations for non-orientable surfaces")
search_arxiv_by_title("Entanglement spectrum and entropy in topological non-Hermitian systems")

