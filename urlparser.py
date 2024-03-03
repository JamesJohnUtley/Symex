import argparse
from urllib.parse import urlparse, parse_qs

def parse_url(url):
    parsed_url = urlparse(url)
    print("Scheme:", parsed_url.scheme)
    print("Netloc:", parsed_url.netloc)
    print("Path:", parsed_url.path)
    
    query_params = parse_qs(parsed_url.query)
    print("Query Params:", query_params)

def main():
    parser = argparse.ArgumentParser(description="Parse a URL and display its components.")
    parser.add_argument("url", help="The URL to parse")
    
    args = parser.parse_args()
    parse_url(args.url)

if __name__ == "__main__":
    main()
