from typing import List, Dict, Union

from telegram import User, Chat

QUOTES_FOUND_TEMPLATE = "{} quotes found."
PERSONS_FOUND_TEMPLATE = "{} persons found."
QUOTE_TEMPLATE = "{}\n" \
                 "~ {}\n" \
                 "{} Brain\n" \
                 "Submitted by {} on {}."
QUOTE_OF_THE_DAY_TEMPLATE = "The quote of the day!\n" \
                            "{}"
ALREADY_SUBSCRIBED_TEMPLATE = "You are already subscribed to the quote of the day at {}."
SUBSCRIPTION_REMOVED_TEMPLATE = "Your subscription for {} was removed."
SUBSCRIPTION_SUCCESSFUL_TEMPLATE = "You will receive the quote of the day every day at {}."
ERROR_COMMAND_TEMPLATE = "An error occurred for command {} by user {}.\n" \
                         "Code: {}"
ERROR_QUERY_TEMPLATE = "An error occurred for query {} by user {}.\n" \
                       "Code: {}"
NO_PERMISSION_REPORT_TEMPLATE = "User {} tried to execute {} without admin privileges."
WHITELIST_REQUEST_TEMPLATE = "User {} with user id {} wants to be whitelisted."
USER_BLACKLISTED_TEMPLATE = "User {} was blacklisted."
USER_WHITELISTED_TEMPLATE = "User {} was whitelisted."
ALREADY_BLACKLISTED_TEMPLATE = "User {} is already blacklisted."
ALREADY_WHITELISTED_TEMPLATE = "User {} is already whitelisted."
BOT_STOPPED_TEMPLATE = "Bot was stopped by {}."


def format_username(user_chat: Union[User, Chat]):
    username = user_chat.first_name
    if user_chat.last_name:
        username += f" {user_chat.last_name}"
    if user_chat.username:
        username += f" (@{user_chat.username})"
    return username


def format_quotes_found(count: int) -> str:
    if count == 0:
        return QUOTES_FOUND_TEMPLATE.format("No")
    return QUOTES_FOUND_TEMPLATE.format(count)


def format_persons_found(count: int) -> str:
    if count == 0:
        return PERSONS_FOUND_TEMPLATE.format("No")
    return PERSONS_FOUND_TEMPLATE.format(count)


def format_quotes(quotes: List[Dict]) -> str:
    res = ""
    for quote in quotes:
        if res != "":
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
    date = quote['date'].replace('-', '/')
    return QUOTE_TEMPLATE.format(text, quoted_persons, brain, quoter, date)


def format_quote_of_the_day(quote_of_the_day: Dict) -> str:
    return QUOTE_OF_THE_DAY_TEMPLATE.format(format_quote(quote_of_the_day))


def format_already_subscribed(time: str) -> str:
    return ALREADY_SUBSCRIBED_TEMPLATE.format(time)


def format_subscription_removed(time: str) -> str:
    return SUBSCRIPTION_REMOVED_TEMPLATE.format(time)


def format_subscription_successful(time: str) -> str:
    return SUBSCRIPTION_SUCCESSFUL_TEMPLATE.format(time)


def format_error_command(command: str, user_chat: Union[User, Chat], code: int) -> str:
    return ERROR_COMMAND_TEMPLATE.format(command, format_username(user_chat), code)


def format_error_query(data: str, user_chat: Union[User, Chat], code: int) -> str:
    return ERROR_QUERY_TEMPLATE.format(data, format_username(user_chat), code)


def format_no_permission_report(user_chat: Union[User, Chat], command: str) -> str:
    return NO_PERMISSION_REPORT_TEMPLATE.format(format_username(user_chat), command)


def format_whitelist_request(user_chat: Union[User, Chat]) -> str:
    return WHITELIST_REQUEST_TEMPLATE.format(format_username(user_chat), user_chat.id)


def format_user_blacklisted(user_chat: Union[User, Chat]) -> str:
    return USER_BLACKLISTED_TEMPLATE.format(format_username(user_chat))


def format_user_whitelisted(user_chat: Union[User, Chat]) -> str:
    return USER_WHITELISTED_TEMPLATE.format(format_username(user_chat))


def format_already_blacklisted(user_chat: Union[User, Chat]) -> str:
    return ALREADY_BLACKLISTED_TEMPLATE.format(format_username(user_chat))


def format_already_whitelisted(user_chat: Union[User, Chat]) -> str:
    return ALREADY_WHITELISTED_TEMPLATE.format(format_username(user_chat))


def format_bot_stopped(user: User):
    return BOT_STOPPED_TEMPLATE.format(format_username(user))


ERROR_OCCURRED = "An error occurred. This problem will be automatically reported to the administrators."
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
NO_PERMISSION = "You do not have permission to do that. This will be reported to the administrators."
WHITELIST_REQUEST_DENIED = "Your whitelist request was denied by an administrator. " \
                           "Please contact an administrator if you do not know why."
WHITELIST_REQUEST_ACCEPTED = "Your whitelist request was accepted by an administrator."
NOT_WHITELISTED = "You are not whitelisted. A whitelist request will be sent to the administrators."
BLACKLISTED = "You are blacklisted. Please contact an administrator if you do not know why."
NO_USER_ID_ARGUMENT = "Please specify the id of the user you want to whitelist."
CANNOT_BLACKLIST_ADMINISTRATOR = "You cannot blacklist an administrator."
PENDING = "Your whitelist request has to be accepted by an administrator before you can interact with this bot."
USER_NOT_FOUND = "User was not found."
UNKNOWN_COMMAND = "Unknown Command."
LOADING = "loading..."
USERNAME = format_username
QUOTES_FOUND = format_quotes_found
PERSONS_FOUND = format_persons_found
QUOTES = format_quotes
QUOTE = format_quote
QUOTE_OF_THE_DAY = format_quote_of_the_day
ALREADY_SUBSCRIBED = format_already_subscribed
SUBSCRIPTION_REMOVED = format_subscription_removed
SUBSCRIPTION_SUCCESSFUL = format_subscription_successful
ERROR_COMMAND = format_error_command
ERROR_QUERY = format_error_query
NO_PERMISSION_REPORT = format_no_permission_report
WHITELIST_REQUEST = format_whitelist_request
USER_BLACKLISTED = format_user_blacklisted
USER_WHITELISTED = format_user_whitelisted
ALREADY_BLACKLISTED = format_already_blacklisted
ALREADY_WHITELISTED = format_already_whitelisted
BOT_STOPPED = format_bot_stopped
