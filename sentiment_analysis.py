#!/usr/bin/python
# Given a list of addon ids, return a verdict of bad or not for each id.
# Usage: sentiment_analysis.py

import csv
import json
import sys
import oauth2 as oauth
from alchemyapi import AlchemyAPI
import urllib2
import time

class BrowserWars:
  """A class to fetch sentiment scores for different keywords."""

  def __init__(self):
    self.KEYWORDS = {
      "firefox" : "browser",
      "mozilla" : "org",
      "google" : "org",
      "chrome" : "browser",
      "internet explorer" : "browser",
      "microsoft" : "org",
      "safari" : "browser",
      "apple": "org"
    }
    self.API_KEY = self.read_api_key(".twitterapikey")
    self.API_SECRET = self.read_api_key(".twitterapisecret")
    self.ACCESS_TOKEN = self.read_api_key(".twitteraccesstoken")
    self.ACCESS_TOKEN_SECRET = self.read_api_key(".twitteraccesstokensecret")
    self.f_out = open("results.csv", "w")
    self.alchemy = AlchemyAPI()
    self.sentiment_results = []

  def read_api_key(self, filename):
    f = open(filename, "r")
    key = f.read().strip()
    f.close()
    return key

  def start(self):
    self.start_time = time.time()
    for i in self.KEYWORDS:
      self.analyze_tweets(i)

  def get_tweets(self, query):
    url = ("https://api.twitter.com/1.1/search/tweets.json?"
           "q=%s&lang=en&locale=en-US&result_type=recent&count=20" % query)
    consumer = oauth.Consumer(key=self.API_KEY, secret=self.API_SECRET)
    token = oauth.Token(key=self.ACCESS_TOKEN, secret=self.ACCESS_TOKEN_SECRET)
    client = oauth.Client(consumer, token)
    response, content = client.request(url, method="GET")
    if int(response["status"]) != 200:
      sys.exit("Didn't get results")
    return content
 
  def analyze_tweets(self, query):
    """Returns the JSON string with the sentiment analysis results."""
    query = urllib2.quote(query)
    twitter_response = self.get_tweets(query)
    self.parse_tweets(twitter_response, query)
    positive, neutral, negative, length = self.calculate_sentiment(query)
    self.f_out.write("%s,%d,%f,%f,%f,%d\n" %
                     (query, self.start_time,
                      positive, neutral, negative, length))

  def parse_tweets(self, twitter_response, query):
    """Parses JSON search results and returns an array of sentiment results"""
    query = urllib2.quote(query)
    twitter_result = json.loads(twitter_response)
    f_results = open("twitter_response_%s.json" % query, "w")
    f_results.write(twitter_response)
    f_results.close()
    if "statuses" not in twitter_result:
      sys.exit("Unknown twitter response %s" % twitter_response)
    statuses = twitter_result["statuses"]
    for s in statuses:
      if "text" not in s:
        sys.exit("Response not ok for query %s %s" % (query, twitter_result))
      escaped = urllib2.quote(s["text"].encode("utf-8"))
      response = self.alchemy.sentiment("text", escaped)
      if response["status"] != "OK":
        sys.exit("Response not ok for query %s %s" % (escaped, response))
      result_obj = {"query": query,
                    "tweet" : escaped,
                    "type" : response["docSentiment"]["type"]}
      if "score" in response["docSentiment"]:
        result_obj["score"] = response["docSentiment"]["score"]
      self.sentiment_results.append(result_obj)

  def calculate_sentiment(self, query):
    m = map(lambda x: x["query"] == query, self.sentiment_results)
    num_positives = sum(map(lambda x: x["type"] == "positive", m))
    num_negatives = sum(map(lambda x: x["type"] == "negative", m))
    num_neutrals = sum(map(lambda x: x["type"] == "neutral", m))
    return (float(num_positives) / len(m),
            float(num_neutrals) / len(m),
            float(num_negatives) / len(m),
            len(m))

def main():
  if len(sys.argv) != 1:
    sys.exit("Usage: sentiment_analysis.py")
  browserwars = BrowserWars()
  browserwars.start()

if __name__ == "__main__":
  main()
