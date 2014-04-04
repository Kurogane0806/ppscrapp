import sys
import gzip
import json
import logging
import requests
import StringIO
import threading
import google_places
import email_scraper
import traceback
from flask import Flask, request, jsonify

logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('email_scraper').setLevel(logging.DEBUG)
logging.basicConfig(filename='log', format='%(asctime)s %(name)s %(levelname)s %(filename)s,%(lineno)d: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

# GOOGLE_API_KEY='AIzaSyCOK72M4rDIx5uCGb-sYq9nB5-WmdqGMvw'
# GOOGLE_API_KEY='AIzaSyBNkWI9SonctAqiGUqOKlMt3yb-mFgblQY'
GOOGLE_API_KEY='AIzaSyD2sr3FFZ3flD8AsooqdVVwNz77t0W7jp0'

app=Flask(__name__)


@app.after_request
def gzip_content(response):
    response.direct_passthrough=False
    accept_encoding=request.headers.get('Accept-Encoding', '')
    if 'gzip' not in accept_encoding.lower():
        return response
    if (200 > response.status_code >= 300) or len(response.data) < 500 or 'Content-Encoding' in response.headers:
        return response
    gzip_buffer=StringIO.StringIO()
    gzip_file=gzip.GzipFile(mode='wb', compresslevel=6, fileobj=gzip_buffer)
    gzip_file.write(response.data)
    gzip_file.close()
    response.data=gzip_buffer.getvalue()
    response.headers['Content-Encoding']='gzip'
    response.headers['Content-Length']=len(response.data)
    return response



class address_components(object):
    '''
    itemize address_components type keys, see: http://paste.ubuntu.com/6668289
    '''
    def __init__(self, adcmps):
        self.adcmps=adcmps
    def __getitem__(self, key):
        t=[i['short_name'] for i in self.adcmps if key in i['types']]
        return t[0] if len(t)>0 else ''


def details_and_emails(place, get_emails):
    '''
    param place: one item of google_places.textsearch_find_more result list
    return: dict, {name, address, website, email1, ...}
    '''
    # place details
    try:
        logger.debug('trying to get details of %s from google'%place['reference'][-8:])
        detail=google_places.place_details(place['reference'], GOOGLE_API_KEY)['result']
        logger.debug('details of %s from googlei retrived'%place['reference'][-8:])
    except:
        logger.debug('details of %s from googlei exception'%place['reference'][-8:])
        return None
    addr=address_components(detail['address_components'])
    res={
        'name': place.get('name', ''),
        'address': place.get('formatted_address', ''),
        'phone': detail.get('international_phone_number', ''),
        'city': addr['locality'],
        'zip': addr['postal_code'],
        'state': addr['administrative_area_level_1'],
        'country': addr['country'],
        'website': detail.get('website', ''),
    }
    for i in res:
        if type(res[i])==unicode:
            continue
        res[i]=res[i].decode('u8', 'ignore')
    # emails
    emails=[]
    if get_emails and res['website']!='':
        try:
            emails=email_scraper.search(res['website'])
            logger.debug("GOT EMAILS FOR %s"%place['reference'][-8:])
        except:
            e = sys.exc_info()[0]
            logger.debug('ERRORS A PLENTY')
            logger.debug(e)
            pass
    emails.extend(['', ''])
    res.update({
        'email1': emails[0],
        'email2': emails[1]
    })
    logger.info('details for: %s (%s)'%(res['name'], place['reference'][-8:]))
    return res


def place_search(query, get_emails):
    '''
    return: list of dict, each dict is result of details_and_emails function
    '''
    def _details(place, q):
        d=details_and_emails(place, get_emails)
        if d==None:
            return
        d['query']=query.decode('u8', 'ignore')
        q.append(d)

    search_result=google_places.textsearch_find_more(query, GOOGLE_API_KEY)
    trd_list=[]
    res_list=[]
    for i in search_result:
        if isinstance(i, google_places.Error):
            raise i
        t=threading.Thread(target=_details, args=(i, res_list))
        trd_list.append(t)
        t.daemon=True
        t.start()
    for t in trd_list:
        t.join()
    return res_list



@app.route('/')
def index():
     return 'It works.'


@app.route('/search', methods=['POST'])
def search():
    phrase=request.form.get('places')
    get_emails=request.form.get('emails')
    get_emails=json.loads(get_emails)
    lines=[line for line in phrase.split('\n') if len(line) > 0]
    res=[]
    for query in lines:
        logger.info('query: %s'%query)
        try:
            r=place_search(query, get_emails)
        except google_places.Error, e:
            logger.error('google_places error: %s'%e)
            return jsonify(result=[{
                'query': query,
                'name': 'ERROR',
                'address': e.message,
            }])
        res.extend(r)
        logger.info('%d results for %s'%(len(r), query))
    return jsonify(result=res)



if __name__=='__main__':
    app.run(host='0.0.0.0', debug=True, port=3000)
