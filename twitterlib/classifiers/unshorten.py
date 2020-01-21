import http.client
import urllib.parse
import re
import pickle
import os.path
from concurrent.futures import ThreadPoolExecutor
import urllib.request


urlfinder = re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|((news|telnet|nttp|file|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+(:[0-9]*)?/[-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]*[^]'\\.}>\\),\\\"]")


url_cache = {}
if os.path.exists('.urlcache.p3'):
    with open('.urlcache.p3', 'rb') as f:
        while True:
            try:
                a,b = pickle.load(f)
                url_cache[a] = b
            except EOFError:
                break


def unshorten(url):
    if url in url_cache:
        return url_cache[url]

    new_url = _unshorten(url)
    with open('.urlcache.p3', 'ab') as f:
        pickle.dump((url, new_url), f)
        url_cache[url] = new_url
    return new_url


def _unshorten(url):
    try:
        parsed = urllib.parse.urlparse(url)
        h = http.client.HTTPConnection(parsed.netloc, timeout=5)
        h.request('HEAD', parsed.path)
        response = h.getresponse()
    except:
        return url

    if response.status//100 == 3:
        for key in response.headers.keys():
            if key.lower() == 'location':
                url_ = response.getheader(key)
                return unshorten(url_) if url_ != url else url_
    return url


def unshorten_in_text(text):
    result = []
    start = 1
    for group in urlfinder.finditer(text):
        a, b = group.span()
        result.extend([
            text[start-1:a],
            unshorten(text[a:b])
        ])
        start = b
    result.append(text[start-1:])
    return ''.join(result)


def unshorten_in_texts(texts):
    with ThreadPoolExecutor(50) as executor:
        return executor.map(unshorten_in_text, texts)


def extract_urls(text):
    for group in urlfinder.finditer(text):
        a, b = group.span()
        yield text[a:b]


def separate_urls(text):
    urls = [unshorten(text[a:b]) for group in urlfinder.finditer(text) for a, b in [group.span()]]
    text = urlfinder.sub(' ', text)
    return text, urls
