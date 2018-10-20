from flask import Flask
from flask import request
from flask import jsonify
from pymemcache.client import base
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, EntitiesOptions, KeywordsOptions

import json
import requests

app = Flask(__name__)

# Mock Stock Tweet Entity List
mock_stock_tweet_list = [
	{"tweeter_handle": "john_doe", "symbol": "GOOG", "tweet": "This company is amazing!", "tweeter_score": 88}, 
	{"tweeter_handle": "tim_doe", "symbol": "GOOG", "tweet": "This company is awesome!", "tweeter_score": 95},
	{"tweeter_handle": "joel_doe", "symbol": "GOOG", "tweet": "This company not good.", "tweeter_score": 42} 
]

# Basic Authentication to access the Watson Natural Language API.
natural_language_understanding = NaturalLanguageUnderstandingV1(
		username='d48b8816-72c8-458b-b479-700406d7c79f',
		password='4roA07z2wfi6',
		version='2018-03-19'
)

cache = base.Client(('localhost', 11211))

@app.route('/')
def get_stock_prediction():
	ticker_symbol = request.args.get("ticker_symbol")

	if not ticker_symbol:
		return jsonify("Please make sure to send a ticker symbol")

	# Fetch from database for ticker - use mock for now.
	# TODO (macliu): Load stock tweets from database for recency.
	prediction_score = cache.get(ticker_symbol)
	if not prediction_score:
		total_score = 0
		count = 0
		print("MISS")
		global mock_stock_tweet_list
		for stock_tweet in mock_stock_tweet_list:
			if stock_tweet["symbol"] == ticker_symbol:
				total_score += get_stock_analysis_score(stock_tweet["tweet"]) * stock_tweet["tweeter_score"]
				count += 1

		if count == 0:
			return jsonify("We have no data on: {}".format(ticker_symbol))

		prediction_score = total_score / count
	else:
		print("HIT")

	# Write to cache
	cache.set(ticker_symbol, prediction_score)

	return jsonify("The score for {} is: {}".format(ticker_symbol, prediction_score))


def get_stock_analysis_score(tweet):
	global natural_language_understanding
	response = natural_language_understanding.analyze(
  		text=tweet,
	  	features=Features(
	    	entities=EntitiesOptions(
	      		emotion=True,
	      		sentiment=True,
	      		limit=2
	      	),
	    	keywords=KeywordsOptions(
	      		emotion=True,
	      		sentiment=True,
	      		limit=2)
	    )
    ).get_result()

	return response["keywords"][0]["sentiment"]["score"]


if __name__ == '__main__':
    app.run()
