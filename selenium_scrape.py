from selenium import webdriver
import os
from pw import pw
import time
from helper import selector, load_jquery, scroll_to_bottom, get_outerhtml, alert
from bs4 import BeautifulSoup


 
def start_driver(base_url):
   path = os.path.join(os.getcwd(), 'chromedriver')
   options = webdriver.ChromeOptions()
   options.add_argument("--start-maximized")
   driver = webdriver.Chrome(executable_path=path, chrome_options=options)
   driver.get(base_url)
   load_jquery(driver)


start_driver('http://store.steampowered.com/')

