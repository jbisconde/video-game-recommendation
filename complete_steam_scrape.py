import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import time
import unirest
import sys
import traceback

'''
    <div id="game_area_metalink">
        <a href="http://www.metacritic.com/game/pc/counter-strike-global-offensive" target="_blank">Read Critic Reviews</a>
        <img src="http://store.akamai.steamstatic.com/public/images/ico/iconExternalLink.gif" border="0" align="bottom">
    </div>
'''

def scrape_steam_data(game_url):
    try:
        content = requests.get(game_url, timeout=10).text
        time.sleep(1)
    except requests.exceptions.RequestException as e:
        print e
        traceback.print_exc(file=sys.stdout)
        return "Request_Error"

    soup = BeautifulSoup(content, 'html.parser')

    try:
        # Get the div for the metacritic link
        meta_link_div = soup.select('div#game_area_metalink')[0]
    except IndexError as e:
        # if the metacritic link doesn't exist, we exit and continue to the next game
        print e
        print "The game doesn't exist in Metacritic."
        # traceback.print_exc(file=sys.stdout)
        return

    game_desc, game_tags = parse_through_steam_soup(soup, game_url)
    
    # Finally do the metacritic link to get user and critic reviews
    try:
        meta_link = meta_link_div.a['href']
    except TypeError as e:
        print e
        print "Metacritic is in Steam, but could not find any link."
        # traceback.print_exc(file=sys.stdout)
        return

    return game_desc, game_tags, meta_link

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
    return game_desc, game_tags

def parse_through_metacritic(meta_link):
    user_link = '/user-reviews'
    critic_link = '/critic-reviews'
    add_pages = '?page='

    meta_user_review_link = meta_link + user_link
    meta_user_review_link_more = meta_user_review_link + add_pages

    meta_critic_review_link = meta_link + critic_link
    meta_critic_review_link_more = meta_critic_review_link + add_pages

    try:
        content = requests.get(meta_user_review_link, timeout=5).text
    except requests.exceptions.RequestException as e:
        print e
        traceback.print_exc(file=sys.stdout)
        return

    soup = BeautifulSoup(content, 'html.parser')
    # Not Working - Metacritic is forbidden

def create_additional_data():
    client = MongoClient()
    db = client['metacritic']
    coll = db['steam_games']
    steam_data = list(coll.find())

    for game in steam_data:
        if ('meta_link' not in game.keys()): # or (not game['game_tags']):
            game_url = str(game['game_link']).split('?')[0]

            mongo_id = game['_id']
            print game_url

            initial_data = scrape_steam_data(game_url)

            if initial_data == "Request_Error":
                continue

            if not initial_data:
                game['meta_link'] = 'None'
                coll.update({'_id':mongo_id}, {"$set": game}, upsert=False)
                continue

            game_desc, game_tags, meta_link = initial_data
            game['game_link'] = game_url
            game['game_desc'] = game_desc
            game['game_tags'] = game_tags
            game['meta_link'] = meta_link
            print meta_link
            coll.update({'_id':mongo_id}, {"$set": game}, upsert=False)
            
    client.close()

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
    response = unirest.get(game_url,
      headers={
        "X-Mashape-Key": "1QxRFuS3QAmshvDGXNOrFirZ70K1p1RZLQOjsniSbuQpk24WB0",
        "Accept": "application/json"
      }
    )
    return response














