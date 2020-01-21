import json
import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


def _extract_attribute(text, attribute, begin=0):
    a = text.find(attribute + '="', begin)
    # if a < 0:
    #     print(text)
    assert a >= 0, "Could not find attribute {}".format(attribute)
    a += len(attribute) + 2
    b = text.find('"', a)
    return text[a:b]


def extract_text(html):
    soup = BeautifulSoup("<p>" + html + "</p>", "lxml")
    return soup.text


def _extract_tweets(text):
    for element in text.split('<li class="js-stream-item stream-item stream-item')[1:]:
        if 'data-tweet-id="' not in element:
            continue
        user_id = _extract_attribute(element, 'data-user-id')
        tweet_id = _extract_attribute(element, 'data-tweet-id')
        screenname = _extract_attribute(element, 'data-screen-name')
        t = datetime.datetime.fromtimestamp(
            int(_extract_attribute(element, 'data-time')))
        at2 = element.find('<p class="TweetTextSize')
        at2 = element.find('>', at2) + 1
        at3 = element.find('</p>', at2)
        tweet = extract_text(element[at2:at3])

        yield {
            'id': tweet_id,
            'tweet': tweet,
            'screenname': screenname,
            'user-id': user_id,
            'time': t
        }


def get_session():
    session = requests.Session()
    session.headers.update({
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-encoding': 'gzip, deflate, sdch, br',
        'accept-language': 'en-US,en;q=0.8,nl;q=0.6',
        'dnt': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
    })
    return session


def crawl_twitter(initial_url_format, xhr_url_format, query):
    """ Scrape twitter by faking a browser setting. `initial_url_format` is
    formatted with the query and specifies the page the browser starts with.
    The scraper then iterates over new tweets by loading the XHR requests
    responsible for infinite scroll behavior on the twitter website.
    `xhr_url_format` is formatted with the query and the data_max_position,
    a pagination variable twitter uses in XHR requests."""
    session = get_session()
    response = session.get(initial_url_format.format(query))
    for user in _extract_tweets(response.text):
        yield user
    max_position = _extract_attribute(response.text, 'data-max-position')

    zero_returns = 0
    while zero_returns < 10:
        url = (xhr_url_format.format(query, max_position))
        response2 = session.get(url)
        data = json.loads(response2.text)
        users = list(_extract_tweets(data['items_html']))
        if len(users) == 0:
            zero_returns += 1
        else:
            zero_returns = 0
        for user in users:
            yield user
        max_position = data['min_position'] if 'min_position' in data else None


def get_tweets_from_user(screenname):
    """ Returns an interator of tweets mentioning the screenname which scrapes twitter by faking a browser session. """
    return crawl_twitter(
        'https://twitter.com/search?q=from%3A{}&src=typd',
        'https://twitter.com/i/search/timeline?vertical=default&q=from%3A{0}&src=typd&include_available_features=1&include_entities=1&max_position={1}&reset_error_state=false',
        screenname)


def get_tweets_from_hashtag(hashtag):
    """ Returns an interator of tweets including the hashtah which scrapes twitter by faking a browser session. """
    return crawl_twitter(
        'https://twitter.com/hashtag/{}?f=tweets&vertical=default',
        'https://twitter.com/i/search/timeline?f=tweets&vertical=default&q=%23{}&include_available_features=1&include_entities=1&max_position={}&reset_error_state=false',
        hashtag)


def get_tweets_from_mention(screenname):
    """ Returns an interator off tweets mentioning the screenname which scrapes twitter by faking a browser session. """
    return crawl_twitter(
        'https://twitter.com/search?q=%40{}',
        'https://twitter.com/i/search/timeline?vertical=default&q=%40{}&include_available_features=1&include_entities=1&max_position={}&reset_error_state=false',
        screenname)


def get_tweets_by_query(query):
    """ Returns an iterator of tweets for the query which scrapes twitter by faking a browser session. """
    query = quote_plus(query)
    return crawl_twitter(
        'https://twitter.com/search?q={}',
        'https://twitter.com/i/search/timeline?vertical=default&q={}&include_available_features=1&include_entities=1&max_position={}&reset_error_state=false',
        query)


def get_conversation_of_tweet_id(id):
    session = get_session()
    data = session.get('https://twitter.com/a/status/{}'.format(id))
    if data.status_code == 404:
        return []
    elements = data.text.split(
        '<div class="tweet js-stream-tweet js-actionable-tweet js-profile-popup-actionable'
    )[1:]
    at = data.text.find('<div class="tweet permalink-tweet js-actionable-user js-actionable-tweet js-original-tweet')
    at0 = data.text.find('>', data.text.find('<p class="TweetTextSize', at)) + 1
    at1 = data.text.find('</p>', at0)
    conversation = [{
        'id': _extract_attribute(data.text, 'data-tweet-id', at),
        'screenname': _extract_attribute(data.text, 'href', at).split('/')[1],
        'user-id': _extract_attribute(data.text, 'data-user-id', at),
        'time': datetime.datetime.fromtimestamp(int(_extract_attribute(data.text, 'data-time', at))),
        'tweet': extract_text(data.text[at0:at1]),
        'main-tweet': True
    }]
    for element in elements:
        at0 = element.find('>', element.find('<p class="TweetTextSize')) + 1
        at1 = element.find('</p>', at0)
        tweet = extract_text(element[at0:at1])
        conversation.append({
            'id': _extract_attribute(element, 'data-tweet-id'),
            'screenname': _extract_attribute(element, 'data-permalink-path').split('/')[1],
            'user-id': _extract_attribute(element, 'data-user-id'),
            'time': datetime.datetime.fromtimestamp(int(_extract_attribute(element, 'data-time'))),
            'tweet': extract_text(tweet),
            'main-tweet': False
        })
    return list(sorted(conversation, key=lambda x: x['time']))
