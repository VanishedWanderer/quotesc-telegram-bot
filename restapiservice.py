import json
from typing import List, Dict

import requests

BASE_URL = 'http://localhost:3001'
QUOTES_PATH = '/quotes'
QUOTES_COUNT_PATH = '/quotes/count'
QUOTES_RANDOM_PATH = '/quotes/random'
QUOTE_OF_THE_DAY_PATH = '/quoteoftheday'


def get_quotes_count(filters: List[str] = '') -> int:
    response = requests.get(BASE_URL + QUOTES_COUNT_PATH)
    if response.ok:
        count = int(response.text)
        return count
    else:
        response.raise_for_status()


def get_quotes(filters: List[str] = '') -> List[Dict]:
    response = requests.get(BASE_URL + QUOTES_PATH)
    if response.ok:
        quotes = json.loads(response.content)
        return quotes
    else:
        response.raise_for_status()


def get_quote_random(filters: List[str] = '') -> Dict:
    response = requests.get(BASE_URL + QUOTES_RANDOM_PATH)
    if response.ok:
        quote = json.loads(response.content)
        return quote
    else:
        response.raise_for_status()


def get_quote_of_the_day() -> Dict:
    response = requests.get(BASE_URL + QUOTE_OF_THE_DAY_PATH)
    if response.ok:
        quote = json.loads(response.content)
        return quote
    else:
        response.raise_for_status()
