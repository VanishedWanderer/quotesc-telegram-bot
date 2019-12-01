from typing import List, Dict

QUOTES_FOUND_TEMPLATE = "{} quotes found"
QUOTE_TEMPLATE = "\"{}\"\n" \
                 "~ {}\n" \
                 "{} Brain\n" \
                 "Submitted by {} on {}"
QUOTE_OF_THE_DAY_TEMPLATE = "The quote of the day!\n" \
                            "{}"
ALREADY_SUBSCRIBED_TEMPLATE = "You are already subscribed to the quote of the day at {}."
SUBSCRIPTION_REMOVED_TEMPLATE = "Your subscription for {} was removed."
SUBSCRIPTION_SUCCESSFUL_TEMPLATE = "You will receive the quote of the day every day at {}."
ERROR_TEMPLATE = "An error occurred for request {} by user {}.\n" \
                 "Code: {}"


def format_quotes_found(count: int) -> str:
    if count == 0:
        return QUOTES_FOUND_TEMPLATE.format("No")
    return QUOTES_FOUND_TEMPLATE.format(count)


def format_quotes(quotes: List[Dict]) -> str:
    res = ""
    for quote in quotes:
        if res == "":
            res += "\n\n"
        res += f"{QUOTE(quote)}"
    return res


def format_quote(quote: Dict) -> str:
    text = quote['quote']
    quoted_persons = ''
    for person in quote['quotedPersons']:
        if quoted_persons != '':
            quoted_persons += ", "
        quoted_persons += f"{person['firstName']} {person['lastName']}"
    brain = int(quote['brain'])
    quoter = f"{quote['quoter']['firstName']} {quote['quoter']['lastName']}"
    date = quote["date"].replace('-', '/')
    return QUOTE_TEMPLATE.format(text, quoted_persons, brain, quoter, date)


def format_quote_of_the_day(quote_of_the_day: Dict) -> str:
    return QUOTE_OF_THE_DAY_TEMPLATE.format(format_quote(quote_of_the_day))


def format_already_subscribed(time: str) -> str:
    return ALREADY_SUBSCRIBED_TEMPLATE.format(time)


def format_subscription_removed(time: str) -> str:
    return SUBSCRIPTION_REMOVED_TEMPLATE.format(time)


def format_subscription_successful(time: str) -> str:
    return SUBSCRIPTION_SUCCESSFUL_TEMPLATE.format(time)


def format_error(request: str, username: str, code: int) -> str:
    return ERROR_TEMPLATE.format(request, username, code)


ERROR_OCCURRED = "An error occurred. This problem will be automatically reported to the administrator."
HELP = \
    """
    yeet
"""
NO_TIME_ARGUMENT = "Please specify the time at which you want to be notified.\n" \
                        "Example: /subscribe 01:00"
INCORRECT_TIME_FORMAT = "Incorrect time format. Please provide a time formatted like hh:mm."
INVALID_HOUR = "The hour has to be between 00 and 23."
INVALID_MINUTE = "The minute has to be between 00 and 59."
NOT_SUBSCRIBED = "You are not subscribed to the quote of the day."
QUOTES_FOUND = format_quotes_found
QUOTES = format_quotes
QUOTE = format_quote
QUOTE_OF_THE_DAY = format_quote_of_the_day
ALREADY_SUBSCRIBED = format_already_subscribed
SUBSCRIPTION_REMOVED = format_subscription_removed
SUBSCRIPTION_SUCCESSFUL = format_subscription_successful
ERROR = format_error
