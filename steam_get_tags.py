import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import time

# http://www.codedisqus.com/0SyWkjUjUP/c-wpf-steam-website-age-verification-skip.html
# 'http://store.steampowered.com/search/results?sort_by=_ASC&page=486&snr=1_7_7_230_7'
# export PATH=$PATH:Google\ Chrome.app
# https://steamdb.info/
# http://blog.yhathq.com/posts/recommender-system-in-r.html

def get_data_from_game(game_url):
    try:
        content = requests.get(game_url).text
        time.sleep(1)
    except ConnectionError:
        return '', ''

    soup = BeautifulSoup(content, 'html.parser')

    # mytags = soup.select('''a[href*="tag/en"]''')
    # tags = set([tag.text.strip() for tag in mytags])
    desc = " ".join([line.text.strip() for line in soup.select('div.game_area_description')])

    if not desc:
        if 'app' in game_url:
            url_split = game_url.split('app')
            game_url_2 = 'agecheck/app'.join(url_split)
        elif 'sub' in game_url:
            url_split = game_url.split('sub')
            game_url_2 = 'agecheck/sub'.join(url_split)

        soup = send_post_request(game_url, game_url_2)
        desc = " ".join([line.text.strip() for line in soup.select('div.game_area_description')])

    mytags = soup.select('a.app_tag') 
    tags = [tag.text.strip().lower() for tag in mytags]

    return desc, tags

def send_post_request(game_url, game_url_2):
    payload = {
        'ageDay': '1',
        'ageMonth': 'January',
        'ageYear': '1990'  # remember me
    }

    session = requests.session()
    r = session.post(game_url_2, data=payload)
    content = session.get(game_url).text
    # content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    r.close()
    session.close()
    return soup

def main_data():
    client = MongoClient()
    db = client['metacritic']
    coll = db['steam_games2']
    steam_data = list(coll.find())
    for game in steam_data:
        if ('game_desc' not in game.keys()):# or (not game['game_tags']):
            game_url = str(game['game_link']).split('?')[0]
            game_desc, game_tags = get_data_from_game(game_url)
            game['game_desc'] = game_desc
            game['game_tags'] = game_tags
            mongo_id = game['_id']
            coll.update({'_id':mongo_id}, {"$set": game}, upsert=False)
            print mongo_id
    # client.close()

def get_all_game_urls(collection):
    base_url = 'http://store.steampowered.com/search/results?sort_by=_ASC&page='
    add_url = '&snr=1_7_7_230_7'
    total_pages = 486

    for i in xrange(1, total_pages + 1):
        page_url = None
        page_url = base_url + str(i) + add_url
        content = requests.get(page_url).text
        time.sleep(2)
        soup = BeautifulSoup(content, 'html5lib')
        results = soup.select('a.search_result_row.ds_collapse_flag')

        for result in results:
            game_dict = {}
            div_values = [div.text.strip() for div in result.select('div')]
            game_dict['game_name'] = div_values[1]
            game_dict['game_date'] = div_values[2]
            game_dict['game_discount'] = div_values[4]
            game_dict['game_price'] = div_values[5]
            game_dict['game_link'] = result['href']
            game_dict['_id'] = 'game_id:' + div_values[1] + str(i)

            print div_values[1]
            insert_game_to_mongodb(collection, game_dict)
            

def insert_game_to_mongodb(collection, dictionary):
    try:
        collection.insert(dictionary, 
            continue_on_error=True)
    except DuplicateKeyError:
        print 'Already inserted' + dictionary['_id']

    total_games = collection.find().count()
    if total_games % 100 == 0:
        print 'There are %d games so far.' % total_games


def main():
    client = MongoClient()
    db = client['metacritic']
    coll = db['steam_games2']
    total_games_before = coll.find().count()
    get_all_game_urls(coll)
    total_games_after = coll.find().count()
    total_inserts = total_games_after - total_games_before

    client.close()
    if total_games_before == total_games_after:
        return 'No items were inserted into MongoDB.'
    else:
        return 'There were %d items inserted to MongoDB.' % total_inserts

