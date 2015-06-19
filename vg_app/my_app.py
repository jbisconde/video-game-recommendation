from flask import Flask, request, render_template
import random
from pymongo import MongoClient

app = Flask(__name__)
STEAM_DATA = None

def data_from_mongodb():
    client = MongoClient()
    db = client['metacritic']
    coll = db['steam_games2']
    steam_data = list(coll.find().limit(6))
    return steam_data

@app.route('/')
def display():
    return render_template('index.html', DATA=STEAM_DATA)

if __name__ == '__main__':
    STEAM_DATA = data_from_mongodb()
    app.run(host='0.0.0.0', port=8080, debug=True)


