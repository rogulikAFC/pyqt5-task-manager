import requests
import random

import bs4


url = 'https://www.plerdy.com/ru/blog/top-215-motivational-quotes/'
request = requests.get(url)

soup = bs4.BeautifulSoup(request.text, 'html.parser')
post = soup.select('.entry-content')[0]
quotations = post.select('li')

quotations_set = [quotation.text for quotation in quotations]


def random_quotation():
    return random.choice(quotations_set)
