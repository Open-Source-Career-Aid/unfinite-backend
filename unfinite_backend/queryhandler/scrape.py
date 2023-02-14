import bs4, requests

def url_filter(url, h3):
    if h3 is None: return False
    if not url.startswith('/url?q=https://'): return False
    if 'google.com/' in url: return False
    return True

def fix_url_and_h3(url, h3):
    end = url.index('&sa=')
    start = url.index('https://')

    return url[start:end], h3.text if h3 is not None else None

def url_title_pair(link):
    return (link.get('href'), link.next.find('h3'))

def google_SERP(search, page=0):

    req = requests.get(f"https://google.com/search?q={search}&page={page}")

    soup = bs4.BeautifulSoup(req.text, "html.parser")

    urls = [url_title_pair(link) for link in soup.find_all('a')]
    urls_filtered = list(map(lambda pair: fix_url_and_h3(*pair), filter(lambda pair: url_filter(*pair), urls)))

    return urls_filtered
