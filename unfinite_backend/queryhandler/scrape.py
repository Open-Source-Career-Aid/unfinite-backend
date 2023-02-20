import bs4, requests, json
from django.apps import apps


#Feedback = apps.get_model('api', 'Feedback')
#SERP = apps.get_model('api', 'SERP')
#SERPItem = apps.get_model('api', 'SERPItem')

def url_filter(url, h3):
    # boolean filter to filter out unwanted Google SERP links
    if h3 is None: return False
    if not url.startswith('/url?q=https://'): return False
    if 'google.com/' in url: return False
    return True

def fix_url_and_h3(url, h3):
    # pulls out the actual resource link, they're strangely formatted by Google
    end = url.index('&sa=')
    start = url.index('https://')

    return url[start:end], h3.text if h3 is not None else None

def url_title_pair(link):
    # takes an <a> object and returns a pair of the url and the h3 object under the <a>,
    # if it exists (might be None)
    return (link.get('href'), link.next.find('h3'))

def google_SERP(search, page=0):

    # makes a request to Google Search with specified search string, and page
    # and returns list of url-title pairs (check type of url_title_pair) 

    req = requests.get(f"https://google.com/search?q={search}&page={page}")

    soup = bs4.BeautifulSoup(req.text, "html.parser")

    urls = [url_title_pair(link) for link in soup.find_all('a')] # gets all of the <a> tags from the page
    urls_filtered = list(map(lambda pair: fix_url_and_h3(*pair), filter(lambda pair: url_filter(*pair), urls)))

    return urls_filtered

# logic will have to be changed when skeletons have more structure
# not used atm. TODO: remove, perhaps
def attach_links(skeleton, query):

    out = []

    for item in skeleton:
        existing = SERP.objects.filter(search_string=item) # can use contains and other more advanced methods in future
        if len(existing) > 0:
            
            # make sure query is tied to existing SERP
            serp_obj = existing[0]
            serp_obj.queries.add(query)
            serp_obj.save()

            serps = json.loads(serp_obj.entries)
            if len(serps) > 0: # should always be the case, I think?
                serp = serps[0]
        else:
            # make new SERP object with results
            serps = google_SERP(item)
            new_serp = SERP(search_string=item, entries=json.dumps(serps))
            new_serp.save()
            new_serp.queries.add(query)
            new_serp.save()

            serp = serps[0] # will need to be more advanced, in the future, just takes top search result
        
        out.append({item: {'title':serp[1], 'url':serp[0]}})

    return out



