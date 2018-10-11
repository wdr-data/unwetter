import os

import tweepy


_auth = tweepy.OAuthHandler(
    os.environ['TWITTER_CONSUMER_KEY'], os.environ['TWITTER_CONSUMER_SECRET'])
_auth.set_access_token(
    os.environ['TWITTER_ACCESS_TOKEN'], os.environ['TWITTER_ACCESS_TOKEN_SECRET'])

api = tweepy.API(_auth)
