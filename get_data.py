# Data Scraping
import requests
from bs4 import BeautifulSoup
import unirest
import pandas as pd
from pymongo import MongoClient

def get_game_reviews(game_name):

    base_url = "https://byroredux-metacritic.p.mashape.com/reviews?"
    metacritic_url_api = base_url + "url=http%3A%2F%2Fwww.metacritic.com%2Fgame%2Fpc%2F" + game_name
    # These code snippets use an open-source library. http://unirest.io/python
    response = unirest.get(metacritic_url_api,
      headers={
        "X-Mashape-Key": "ac4LUqV2kPmshRCn8PzU4DDRrVF1p1nHzfrjsnvVX6j91VAYNi",
        "Accept": "application/json"
      }
    )
    return response

def insert_one_to_mongo(coll, review_json):
    try:
        coll.insert(review_json, 
            continue_on_error=True)
    except:
        pass

    total_reviews = coll.find().count()
    if total_reviews % 100 == 0:
        print 'There are %d reviews so far.' % total_reviews

def insert_reviews_to_mongo(coll, unirest_json, game_name):

    reviews = unirest_json.body['result']
    
    for review in reviews:
        review['game_name'] = game_name
        insert_one_to_mongo(coll, review)

def get_top_100_games(coll):
    metacritic_url = "http://www.metacritic.com/browse/games/score/metascore/all/pc"

    content = requests.get(metacritic_url).content
    soup = BeautifulSoup(content)

    mydivs = soup.findAll('div', class_="product_item product_title")

    for div in mydivs:
        link = div.a['href']
        game_name = link.split('/')[-1]
        
        # Get the reviews for each game
        response = get_game_reviews(game_name)

        # Insert the reviews to MongoDB
        insert_reviews_to_mongo(coll, response, game_name)

def get_data_from_mongodb():
    client = MongoClient()
    db = client.metacritic
    coll = db.reviews

    games_coll = list(coll.find())
    games_df = pd.DataFrame(games_coll)

    client.close()
    print 'There are %d reviews from MongoDB.' % len(games_df)
    return games_df

def main():
    # use metacritic
    # db.createCollection("reviews")
    client = MongoClient()
    db = client.metacritic
    coll = db.reviews

    total_reviews_before = coll.find().count()
    get_top_100_games(coll)
    total_reviews_after = coll.find().count()
    total_inserts = total_reviews_after - total_reviews_before

    client.close()
    if total_reviews_before == total_reviews_after:
        return 'No items were inserted into MongoDB.'
    else:
        return 'There were %d items inserted to MongoDB.' % total_inserts


if __name__ == '__main__':
    comment = main()
    print comment






