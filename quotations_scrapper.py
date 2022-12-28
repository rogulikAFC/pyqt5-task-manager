import requests
import random

import bs4


url = 'https://www.plerdy.com/ru/blog/top-215-motivational-quotes/'
request = requests.get(url)

# Поиск элемента с цитатой
soup = bs4.BeautifulSoup(request.text, 'html.parser')
post = soup.select('.entry-content')[0]
quotations = post.select('li')

# генерация списка с цитатами
quotations_set = [quotation.text for quotation in quotations]


def random_quotation() -> str:
    """
    Рандомная цитата
    """
    return random.choice(quotations_set)
