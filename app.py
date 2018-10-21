from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from pymemcache.client import base
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, EntitiesOptions, KeywordsOptions

import json
import requests
import psycopg2

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
conn = psycopg2.connect(database="hack-isu", user="postgres", password="twitterbot1", host="35.232.221.83", port="5432")

@app.route('/')
@app.route('/index.html')
def get_dashboard():
	return render_template('index.html')

@app.route('/get_stock_prediction')
def get_stock_prediction():
	ticker_symbol = request.args.get("ticker_symbol")

	if not ticker_symbol:
		return jsonify("Please make sure to send a ticker symbol")
	   
	prediction_score = None#cache.get(ticker_symbol)
	top_tweets = []
	if not prediction_score:
		total_score = 0
		positive_count = 0
		neutral_count = 0
		negative_count = 0
		cur = conn.cursor()
		cur.execute("SELECT * from public.tweets where ticker='{}';".format(ticker_symbol))
		stock_tweet_list = cur.fetchall()
		print(stock_tweet_list)
		for stock_tweet in stock_tweet_list:
			score = get_stock_analysis_score(stock_tweet[2])

			if score > 0:
				positive_count += 1
				if score > 1:
					top_tweets.append(stock_tweet)
			elif score < 0:
				negative_count += 1;
			else:
				neutral_count += 1;

			total_score += score * stock_tweet[3]

		count = positive_count + neutral_count + negative_count
		if count == 0:
			return jsonify("We have no data on: {}".format(ticker_symbol))

		prediction_score = total_score / count

	# Write to cache
	#cache.set(ticker_symbol, prediction_score)

	return render_template('index.html', ticker=ticker_symbol, score=prediction_score, positive_count=positive_count, negative_count=negative_count)

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
