import re
import bs4
import urlparse
import requests
import logging

logger=logging.getLogger(__name__)

class EmailScraper(object):

    def __init__(self):
        pass


    def find_emails(self, init_url):
        page=self.get_url(init_url)
        # open('/tmp/page1', 'wb').write(page.encode('u8'))
        emails=self.find_emails_in_page(page)
        urls=self.find_contact_us_urls(page)
        for url in urls:
            if url.lower().startswith('mailto:'):
                pass#continue
            url=urlparse.urljoin(init_url, url)
            # FIXME: can not detect urls like this: "mailto:info@example.com"
            try:
                page=self.get_url(url)
            except Exception, err:
                logger.debug('Exception fetching contact us url!')
                logger.warn([err, init_url])
                continue
            emails.extend(self.find_emails_in_page(page))
        emails=list(set(emails))
        emails=self.email_ranking(emails)
        logger.info('%d emails for %s'%(len(emails), init_url))
        return emails


    def email_ranking(self, emails):
        '''
        this method try to sort emails based on it's usefulness.
        For example info@ is better than bizdev@
        param emails: list of emails
        return: list of emails
        '''
        def rank(e):
            s=e[:e.find('@')]
            if s=='info': return 99
            if s=='support': return 98
            if s=='sales': return 97
            return 96-len(s)
        def cmpr(x, y):
            return cmp(rank(x), rank(y))
        l=emails[:]
        l.sort(cmpr, reverse=True)
        return l


    def get_url(self, url):
        '''
        param url: url string
        return: html page as string
        '''
        logger.debug('get_url: %s'%url)
        try:
            r=requests.get(url, timeout=7)
            logger.debug('url (%s) retrived %d bytes'%(url, len(r.text)))
            return r.text
        except requests.exceptions.Timeout:
            logger.debug('get url (%s) timeout'%url)
            return ''


    def find_emails_in_page(self, page):
        '''
        param page: an html string not a url
        return: list of emails
        '''
        page=page.replace('&#64;', '@')
        return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}", page)


    def find_contact_us_urls(self, page):
        '''
        param page: an html string not a url
        return: list of urls
        '''
        def t(s):
            if s is None:
                return False
            if 'contact' in s.lower():
                return True
            if 'about' in s.lower():
                return True
            return False
        x=bs4.BeautifulSoup(page)
        x=x.find_all(text=t)
        l=[]
        for i in x:
            tag=i
            while tag is not None:
                if tag.name=='a':
                    l.append(tag['href'])
                    break
                tag=tag.parent
        l=list(set(l))
        logger.debug('contact us: %s'%l)
        return l


def search(url):
    s=EmailScraper()
    return s.find_emails(url)


def test():
    # url='http://www.ballengercreekdental.com/'
    url='http://solutionreach.com'
    print search(url)


if __name__=='__main__':
    test()
