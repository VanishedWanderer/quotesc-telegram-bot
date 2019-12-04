import json
import logging
import time
from typing import List, Dict

import requests

session = requests.Session()

ACCEPT_APPLICATION_JSON = {'Accept': 'application/json'}
CONTENT_TYPE_APPLICATION_JSON = {'Content-Type': 'application/json'}
BASE_URL = 'http://localhost:3001'
QUOTES_PATH = '/quotes'
QUOTES_COUNT_PATH = '/count'
QUOTES_RANDOM_PATH = '/random'
QUOTE_OF_THE_DAY_PATH = '/quoteoftheday'
PERSONS_PATH = '/persons'


def timed(call):
    def func(*args, **kwargs):
        start = time.time()
        result = call(*args, **kwargs)
        end = time.time()

        logging.info(f"{call.__name__} took {(end - start):.2f} seconds.")

        return result

    return func


@timed
def get_quotes_count(filters: List[str] = None) -> int:
    response = session.get(url=BASE_URL + QUOTES_COUNT_PATH,
                           headers=ACCEPT_APPLICATION_JSON)
    if response.ok:
        count = response.json()
        return count['count']
    else:
        response.raise_for_status()


@timed
def get_quotes(filters: List[str] = None, page: int = 1, count: int = 0) -> List[Dict]:
    params = {
        '_page': page,
        '_limit': count
    }
    response = session.get(url=BASE_URL + QUOTES_PATH,
                           headers=ACCEPT_APPLICATION_JSON,
                           params=params)
    if response.ok:
        quotes = response.json()
        return quotes
    else:
        response.raise_for_status()


@timed
def get_quote_random(filters: List[str] = None) -> Dict:
    response = session.get(url=BASE_URL + QUOTES_RANDOM_PATH,
                           headers=ACCEPT_APPLICATION_JSON)
    if response.ok:
        quote = response.json()
        return quote
    else:
        response.raise_for_status()


@timed
def get_quote_of_the_day() -> Dict:
    response = session.get(url=BASE_URL + QUOTE_OF_THE_DAY_PATH,
                           headers=ACCEPT_APPLICATION_JSON)
    if response.ok:
        quote = response.json()
        return quote
    else:
        response.raise_for_status()


@timed
def get_persons(filters: List[str] = None) -> List[Dict]:
    response = session.get(url=BASE_URL + PERSONS_PATH,
                           headers=ACCEPT_APPLICATION_JSON)
    if response.ok:
        persons = response.json()
        return persons
    else:
        response.raise_for_status()


@timed
def post_quote(quote: Dict) -> None:
    response = session.post(url=BASE_URL + QUOTES_PATH,
                            data=json.dumps(quote),
                            headers=CONTENT_TYPE_APPLICATION_JSON)
    if not response.ok:
        response.raise_for_status()
