import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import time
from selenium import webdriver
from helper import selector, load_jquery, scroll_to_bottom, get_outerhtml, alert
import os

# http://www.codedisqus.com/0SyWkjUjUP/c-wpf-steam-website-age-verification-skip.html
# 'http://store.steampowered.com/search/results?sort_by=_ASC&page=486&snr=1_7_7_230_7'
# export PATH=$PATH:Google\ Chrome.app
def start_driver(base_url):
   path = os.path.join(os.getcwd(), 'chromedriver')
   options = webdriver.ChromeOptions()
   options.add_argument("--start-maximized")
   driver = webdriver.Chrome(executable_path=path, chrome_options=options)
   driver.get(base_url)
   load_jquery(driver)

def get_data_from_game(game_url):
    content = requests.get(game_url).text
    time.sleep(2)
    soup = BeautifulSoup(content, 'html5lib')

    # mytags = soup.select('''a[href*="tag/en"]''')
    # tags = set([tag.text.strip() for tag in mytags])
    try:
        desc = soup.select('div.game_area_description')[0].text.strip()
        
    except:
        url_split = game_url.split('app')
        game_url = 'agecheck/app'.join(url_split).split('?')[0]

        soup = send_post_request(game_url)
        desc = soup.select('div.game_area_description')[1].text.strip()
        pass


    mytags = soup.select('a.app_tag') 
    tags = [tag.text.strip().lower() for tag in mytags]

    return desc, tags

def send_post_request(game_url):
    payload = {
        'ageDay': '1',
        'ageMonth': 'January',
        'ageYear': '1990'  # remember me
    }

    session = requests.session()
    r = requests.post(game_url, data=payload)
    time.sleep(1)
    content = r.content
    soup = BeautifulSoup(content, 'lxml')
    r.close()
    session.close()
    return soup


def main_data():
    client = MongoClient()
    db = client['metacritic']
    coll = db['steam_games2']
    steam_data = list(coll.find())
    for game in steam_data:
        game_url = game['game_link']
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

