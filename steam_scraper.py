import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from collections import defaultdict
from pymongo.errors import DuplicateKeyError
import cPickle as pickle
from operator import itemgetter
import time
import unirest
import sys
import traceback
import os
import re
import urllib

# Helper functions
def send_post_request(game_url, game_url_2):
    payload = {
        'ageDay': '1',
        'ageMonth': 'January',
        'ageYear': '1990'  # remember me
    }
    # Create a session for the cookie
    session = requests.session()
    # Send the payload to the url
    r = session.post(game_url_2, data=payload)
    # Get the content afterwards
    content = session.get(game_url).text
    # Parse through the content using bs4
    soup = BeautifulSoup(content, 'html.parser')
    # Close the session
    r.close()
    session.close()
    # Return the soup object to parse later
    return soup


def parse_through_steam_soup(soup, game_url):
    # Get the game description
    game_desc = " ".join([line.text.strip() for line in soup.select('div.game_area_description')])

    # If it doesn't exist, check if you need to send a payload for agecheck
    if not game_desc:
        # Do this if the link is an app
        if 'app' in game_url:
            url_split = game_url.split('app')
            game_url_2 = 'agecheck/app'.join(url_split)
        # Otherwise, do the sub
        elif 'sub' in game_url:
            url_split = game_url.split('sub')
            game_url_2 = 'agecheck/sub'.join(url_split)

        # Send a post request with age payload to get the data
        soup = send_post_request(game_url, game_url_2)

        # Get the right game description
        game_desc = " ".join([line.text.strip() for line in soup.select('div.game_area_description')])

    # Get the game tags
    tags = soup.select('a.app_tag')
    # Get the text values from the game tags html
    game_tags = [tag.text.strip() for tag in tags]

    # Return the description and tags
    return game_desc, game_tags, soup

    
def scrape_steam_data(game_url):
    try:
        content = requests.get(game_url, timeout=10).text
        time.sleep(1)
    except requests.exceptions.RequestException as e:
        print e
        traceback.print_exc(file=sys.stdout)
        return "Request_Error"

    soup = BeautifulSoup(content, 'html.parser')

    age_check = soup.find('input', {'name': 'snr'})['value']

    # For future use
    # if 'agecheck' in age_check:
    #     game_desc, game_tags, soup = parse_through_steam_soup(soup, game_url)
    # else:
    game_desc, game_tags, soup = parse_through_steam_soup(soup, game_url)
    
    try:
        # Get the div for the metacritic link
        meta_link_div = soup.select('div#game_area_metalink')[0]
    except IndexError as e:
        # if the metacritic link doesn't exist, we exit and continue to the next game
        print e
        print "The game doesn't exist in Metacritic."
        # traceback.print_exc(file=sys.stdout)
        return

    # Finally do the metacritic link to get user and critic reviews
    try:
        meta_link = meta_link_div.a['href']
    except TypeError as e:
        print e
        print "Metacritic is in Steam, but could not find any link."
        # traceback.print_exc(file=sys.stdout)
        return
    return game_desc, game_tags, meta_link


def get_metacritic_reviews(meta_link, user=True):
    base_url = "https://byroredux-metacritic.p.mashape.com/"
    user_url = "user-reviews"
    critic_url = "reviews"
    end_url = "url=http%3A%2F%2Fwww.metacritic.com%2Fgame%2Fpc%2F"
    if user:
        mashape_url = base_url + user_url + "?page_count=5&" + end_url
    else:
        mashape_url = base_url + critic_url + "?" + end_url

    # These code snippets use an open-source library. http://unirest.io/python
    game_url = mashape_url + meta_link.split('/')[-1]
    response = requests.get(game_url,
      headers={
        "X-Mashape-Key": "h8QdBav6HZmshk9E8AoErg4L9EIqp1zKztVjsnFMz5bYpqC0iY",
        "Accept": "application/json"
      }, timeout=100
    )
    return response

def wilson_confidence(ups, downs):
    n = ups + downs

    if n == 0:
        return 0

    z = 1.96 #1.44 = 85%, 1.96 = 95%
    phat = float(ups) / n
    return ((phat + z * z / ( 2 * n) - z * sqrt( (phat * ( 1 - phat) + z * z / (4 * n)) / n )) / ( 1 + z * z / n ))

class Steam_Scraper(object):

    def __init__(self, collection_name="steam_games", scrape_type=None):
        self.scrape_type = scrape_type
        self.connect_to_mongodb(collection_name=collection_name)

    def connect_to_mongodb(self, collection_name):
        self.client = MongoClient()
        self.database = self.client['metacritic']
        self.collection = self.database[collection_name]

    def close_mongodb(self):
        self.client.close()

    def initial_get_all_steam_games(self):
        total_games_before = self.collection.find().count()

        # Get all the data from steam
        self.get_all_steam_game_data()

        total_games_after = self.collection.find().count()
        total_inserts = total_games_after - total_games_before

        if total_games_before == total_games_after:
            print 'No items were inserted into MongoDB.'
        else:
            print 'There were %d items inserted to MongoDB.' % total_inserts


    def get_all_steam_game_data(self):
        base_url = 'http://store.steampowered.com/search/results?sort_by=_ASC&page='
        total_pages = 489

        for i in xrange(1, total_pages + 1):
            page_url = None
            page_url = base_url + str(i) #+ add_url
            content = requests.get(page_url).text
            # time.sleep(2)
            soup = BeautifulSoup(content, 'html.parser')
            results = soup.select('a.search_result_row.ds_collapse_flag')

            for result in results:
                game_dict = {}
                div_values = [div.text.strip() for div in result.select('div')]
                game_dict['game_name'] = div_values[1]
                game_dict['game_date'] = div_values[2]
                game_dict['game_discount'] = div_values[4]
                game_dict['game_price'] = div_values[5]
                game_dict['game_link'] = result['href']
                game_dict['_id'] = 'game_id:' + div_values[1]

                print div_values[1]
                self.insert_game_data_to_mongodb(dictionary=game_dict)


    def insert_game_data_to_mongodb(self, dictionary, dest_collection=None, insert_type="update"):

        mongo_id = dictionary['_id']
        # Update the current collection
        if (insert_type == "update") and (dest_collection is None):
            game_name = dictionary['game_name']
            self.collection.update({'game_name': game_name}, {"$set": dictionary}, upsert=False)
        # Insert to the current collection
        elif (insert_type == "insert") and (dest_collection is None):
            try:
                self.collection.insert(dictionary, 
                    continue_on_error=True)
            except DuplicateKeyError:
                print 'Already inserted' + mongo_id

            total_count = self.collection.find().count()
            if total_count % 100 == 0:
                print 'There are %d so far.' % total_count
        # Insert to the new destination collection
        elif insert_type == "insert":
            try:
                dest_collection.insert(dictionary, 
                    continue_on_error=True)
            except DuplicateKeyError:
                print 'Already inserted' + mongo_id

            total_count = dest_collection.find().count()
            if total_count % 100 == 0:
                print 'There are %d so far.' % total_count
        # Update to the new destination collection
        else:
            mongo_id = dictionary['_id']
            dest_collection.update({'_id': mongo_id}, {"$set": dictionary}, upsert=False)


    # Get the description, game tags and metacritic link from the steam url
    def get_additional_steam_data(self):
        steam_data = list(self.collection.find())

        for game in steam_data:
            # If there is no metacritic link
            if not game['meta_link']:
                game_url = str(game['game_link']).split('?')[0]

                mongo_id = game['_id']
                print game_url
                # Scrape steam to get the game data
                initial_data = scrape_steam_data(game_url)
                # If there was a connection error, don't update the game data
                if initial_data == "Request_Error":
                    continue
                # If there is no metacritic link, set the metacritic link to None
                if not initial_data:
                    game['meta_link'] = 'None'
                    self.collection.update({'_id':mongo_id}, {"$set": game}, upsert=False)
                    continue
                # Otherwise update all the following fields
                game_desc, game_tags, meta_link = initial_data
                game['game_link'] = game_url
                game['game_desc'] = game_desc
                game['game_tags'] = game_tags
                game['meta_link'] = meta_link
                print meta_link, '\n'
                self.collection.update({'_id':mongo_id}, {"$set": game}, upsert=False)


    def aggregate_metacritic_data(self, game, user_status, critic_status):
        if user_status:
            user_data = game['user_review']
            total_user_reviews = user_data['count']

            if total_user_reviews:
                user_reviews = pd.DataFrame(user_data['reviews'])
                user_reviews.loc[:, 'score'] = user_reviews.loc[:, 'score'].astype(float)

                avg_user_reviews = user_reviews['score'].mean()
                game['total_user_reviews'] = total_user_reviews
                game['avg_user_reviews'] = avg_user_reviews
            else:
                game['total_user_reviews'] = 0
                game['avg_user_reviews'] = ''

        if critic_status:
            critic_data = game['critic_review']
            total_critic_reviews = critic_data['count']

            if total_critic_reviews:
                critic_reviews = pd.DataFrame(critic_data['result'])
                critic_reviews.loc[:, 'score'] = critic_reviews.loc[:, 'score'].astype(float)

                avg_critic_reviews = critic_reviews['score'].mean()
                game['total_critic_reviews'] = total_critic_reviews
                game['avg_critic_reviews'] = avg_critic_reviews
            else:
                game['total_critic_reviews'] = 0
                game['avg_critic_reviews'] = ''
        return game


    def get_metacritic_data(self):
        steam_data = list(self.collection.find( {"meta_link": {"$ne": "None"}} ))

        for game in steam_data:
            mongo_id = game['_id']
            # Get the metacritic link
            meta_link = game['meta_link']
            # If there are no user views in the data, do the following
            if 'user_review' not in game.keys():
                # Get the user reviews
                user_response = get_metacritic_reviews(meta_link)
                if user_response.ok:
                    game['user_review'] = user_response.json()

                # Get the critic reviews
                critic_response = get_metacritic_reviews(meta_link, user=False)
                if critic_response.ok:     
                    game['critic_review'] = critic_response.json()

                # If there are any data from users or critics, update the game data
                if user_response.ok or critic_response.ok:
                    game = self.aggregate_metacritic_data(game, user_response.ok, critic_response.ok)

                    self.collection.update({'_id':mongo_id}, {"$set": game}, upsert=False)

                print mongo_id
                print "User Review Status:", user_response.ok
                print "Critic Review Status:", critic_response.ok, '\n'


    def get_steam_image_data(self):
        # images folder has to be in the current directory
        images_list = os.listdir('images')
        steam_data = list(self.collection.find( {"meta_link": {"$ne": "None"}} ))

        for game in steam_data:
            # check and get the type if the link for the image is app or sub
            img_type = game['game_link'].split('/')
            img_url = "http://cdn.akamai.steamstatic.com/steam/" + img_type[3] + "s/" + img_type[4] + "/header.jpg"
            # check the name if it's already there
            check_image = img_type[3] + '_' + img_type[4] + '.jpg'
            save_file = 'images/' + check_image

            # check if the image is already in the folder, and save the image (img_url) to the image location (save_file)
            if check_image not in images_list:
                urllib.urlretrieve(img_url, save_file)


    def create_all_tags(self, collection_name):
        all_games = list(self.collection.find({'user_review': {"$exists": "true"},
                                    'game_name': {'$not': re.compile("Demo")}
                                    }))
        tags_dict = defaultdict(dict)
        for game in all_games:
            for tag in game['game_tags']:
                if tag not in tags_dict.keys():
                    tags_dict[tag]['game_names'] = []
                    tags_dict[tag]['count'] = 0

                tags_dict[tag]['game_names'].append(game['game_name'])
                tags_dict[tag]['count'] += 1

        dest_collection = self.database[collection_name]

        for tag, tag_data in tags_dict.iteritems():
            tag_data['_id'] = tag
            self.insert_game_data_to_mongodb(dictionary=tag_data, dest_collection=dest_collection, insert_type="insert")


    def limit_game_data(self, game=None, save_file=False):

        self.collection.ensure_index([('total_user_reviews', -1), ('avg_user_reviews', -1)])
        if game is None:
            all_games = list(
                self.collection.find({'user_review': {'$exists': 'true'}, 
                            'total_user_reviews': {'$ne': 0},
                            'game_name': {'$not': re.compile("Demo")} }, 
                {
                'game_name': 1, 'game_date':1, 'game_desc':1, 
                'game_tags':1, 'game_price':1, 'game_discount':1, 
                'game_link':1, 'meta_link':1, 'total_user_reviews':1, 
                'avg_user_reviews':1, 'total_critic_reviews':1, 'avg_critic_reviews':1
                })
                .sort([('total_user_reviews', -1), ('avg_user_reviews', -1)])
                #.limit(1000)
                )
            for game in all_games:
                pos = game['avg_user_reviews'] * game['total_user_reviews']
                neg = (10 - game['avg_user_reviews']) * game['total_user_reviews']
                game['confidence'] = round(wilson_confidence(pos / 10, neg / 10), 4)

            all_games = sorted(all_games, 
                key=itemgetter('confidence'), 
                reverse=True)

        else:
            all_games = list(self.collection.find({'user_review': {'$exists': 'true'}, 
                            'total_user_reviews': {'$ne': 0},'game_name': game},
                {
                'game_name': 1, 'game_date':1, 'game_desc':1, 
                'game_tags':1, 'game_price':1, 'game_discount':1, 
                'game_link':1, 'meta_link':1, 'total_user_reviews':1, 
                'avg_user_reviews':1, 'total_critic_reviews':1, 'avg_critic_reviews':1
                }))

        for game in all_games:
            game['avg_user_reviews'] = game['avg_user_reviews'] / 2.
            tags = game['game_tags']
            if len(tags) > 5:
                tags = tags[:5]
                game['game_tags'] = tags
        
        if save_file:
            with open('data/all_games.pkl', 'wb') as f:
                pickle.dump(all_games, f)
        else:
            return all_games


    def limit_tag_data(self, new_collection="steam_tags", save_file=False):
        new_collection = self.database[new_collection]

        all_tags = list(new_collection.find()
                            .sort('count', -1)
                            .limit(20))

        tag_dict = defaultdict(list)
        # get all game info about the tag
        for tag in all_tags:
            tag_id = tag['_id']
            all_games_in_tag = tag['game_names']

            # get the game info about the game
            for game in all_games_in_tag:
                game_data = self.limit_game_data(game=game)
                if game_data:
                    game_data = game_data[0]
                    pos = game_data['avg_user_reviews'] * game_data['total_user_reviews']
                    neg = (10 - game_data['avg_user_reviews']) * game_data['total_user_reviews']
                    game_data['confidence'] = round(wilson_confidence(pos / 10, neg / 10), 4)
                    tag_dict[tag_id].append(game_data)
        
        # Sort the data based on total user views and average user reviews
        for tag, data in tag_dict.iteritems():
            tag_dict[tag] = sorted(data, 
                                key=itemgetter('confidence'), 
                                reverse=True)
        # save all the steam tag data to pickle if needed
        if save_file:
            with open('data/all_tags.pkl', 'wb') as f:
                pickle.dump(tag_dict, f)
        # Otherwise, return the data
        else:
            return tag_dict






