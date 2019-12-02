import json
from typing import List, Dict

import requests

BASE_URL = 'http://localhost:3001'
QUOTES_PATH = '/quotes'
QUOTES_COUNT_PATH = '/count'
QUOTES_RANDOM_PATH = '/random'
QUOTE_OF_THE_DAY_PATH = '/quoteoftheday'
PERSONS_PATH = '/persons'


def get_quotes_count(filters: List[str] = '') -> int:
    response = requests.get(BASE_URL + QUOTES_COUNT_PATH)
    if response.ok:
        count = json.loads(response.content)
        return count['count']
    else:
        response.raise_for_status()


def get_quotes(filters: List[str] = '', page: int = 1, count: int = 0) -> List[Dict]:
    params = {
        '_page': page,
        '_limit': count
    }
    response = requests.get(url=BASE_URL + QUOTES_PATH,
                            params=params)
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


def get_persons() -> List[Dict]:
    response = requests.get(BASE_URL + PERSONS_PATH)
    if response.ok:
        persons = json.loads(response.content)
        return persons
    else:
        response.raise_for_status()
