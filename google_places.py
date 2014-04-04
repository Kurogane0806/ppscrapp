import time
import json
import random
import logging
import requests
import threading


logger=logging.getLogger(__name__)


class Error(Exception):
    pass


def textsearch(query, api_key, location=None, radius=None, pagetoken=None):
    '''
    param query: query is something like 'teacher in ca'. if location is not None the 'in ca' part will be omitted.
    param locaten: {lat, lng}
    return: dict, search responses of google place search, e.g. http://paste.ubuntu.com/6667420
        see: https://developers.google.com/places/documentation/search
    '''
    logger.info('textsearch: q="%s" loc=%s rad=%s page=%s'%(
        query, '' if location==None else '%s:%s'%(location['lat'], location['lng']),
        '' if radius==None else radius, pagetoken[-4:] if pagetoken else ''))
    url="https://maps.googleapis.com/maps/api/place/textsearch/json?query=%s&sensor=false&key=%s"
    if location:
        query=query[:query.find(' in ')]
    url=url%(query, api_key)
    if location:
        url+='&location=%s,%s'%(location['lat'], location['lng'])
    if radius:
        url+='&radius=%s'%radius
    if pagetoken:
        url+="&pagetoken=%s"%pagetoken
    r=requests.get(url)
    res=json.loads(r.text)
    if res['status']!='OK':
        raise Error(res['status'])
    # print 'result items: %d'%len(res['results'])
    return res


def textsearch_all_pages_results(query, api_key, location=None, radius=None):
    '''
    google places returns up to 60 result in 3 pages. this function calls textsearch a few times to retrive all results.
    args are just like textsearch function.
    the next page on google is not valid immediately. it needs about 2 seconds between each page request.
    return: list, the 'results' value of search response (http://paste.ubuntu.com/6667420)
    '''
    results=[]
    next_page_token=None
    is_there_next_page=True
    while is_there_next_page:
        page=textsearch(query, api_key, location, radius, next_page_token)
        results.extend(page['results'])
        next_page_token=page.get('next_page_token')
        if not next_page_token:
            is_there_next_page=False
        else:
            time.sleep(2)
    return results


def place_details(reference, api_key):
    '''
    param reference: str, reference id from place search results
    return: dict, e.g. http://paste.ubuntu.com/6668289
    '''
    url="https://maps.googleapis.com/maps/api/place/details/json?reference=%s&sensor=false&key=%s"
    url=url%(reference, api_key)
    r=requests.get(url)
    res=json.loads(r.text)
    return res


def textsearch_find_more(query, api_key):
    '''
    this function uses textsearch_all_pages_results and tries to find more than 60 results.
    it works via searching the query on multiple locations. each location is location of a valid results itself.
    return: list, the 'results' value of search response (http://paste.ubuntu.com/6667420)
    '''
    more_tries_num=10
    more_tries_radius=1000

    def _search(location, q):
        try:
            res=textsearch_all_pages_results(query, api_key, location, more_tries_radius)
            q.append(res)
        except Error, e:
            q.append(e)
    
    results=[]
    res=textsearch_all_pages_results(query, api_key)
    results.extend(res)

    random_tries=[random.choice(results) for i in range(more_tries_num)]
    trd_list=[]
    res_list=[]
    for i in random_tries:
        t=threading.Thread(target=_search, args=(i['geometry']['location'], res_list))
        trd_list.append(t)
        t.daemon=True
        t.start()
    for t in trd_list:
        t.join()
    for i in res_list:
        results.extend(i)
    
    final=[]
    ids=[]
    for i in results:
        if i['id'] not in ids:
            final.append(i)
            ids.append(i['id'])
            
    # print len(results), len(ids)
    return final
    

def test():
    api_key=''
    query='teacher in ca'
    r=textsearch_find_more(query, api_key)
    print 'all results: ', len(r)


if __name__=='__main__':
    test()
