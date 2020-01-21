import time
import tweepy


def sleep(wait_time=900):
    time.sleep(wait_time)


def _pause_on_limit(api, cursor, wait_time=900, threshold=5):
    while True:
        if (api.rate_limit_status()
            ['resources']['statuses']
            ['/statuses/user_timeline']['remaining']
                < threshold):
            sleep(wait_time=wait_time)
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            sleep(wait_time=wait_time)


def get_tweets_for_handle(api, handle):
    pages = tweepy.Cursor(api.user_timeline,
                          screen_name=handle, count=200).pages()
    for page in _pause_on_limit(api, pages):
        for tweet in page:
            yield tweet
