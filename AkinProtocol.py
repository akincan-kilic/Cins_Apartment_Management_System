from ClientCard import ClientCard

DELIMITER = "@@|<<!?!>>|@@"

WEATHER = "WTH"
CURRENCY = "CUR"
SUBSCRIBE = "SUB"
UNSUBSCRIBE = "USB"

WEATHER_GET = f"{WEATHER}{DELIMITER}"
CURRENCY_GET = f"{CURRENCY}{DELIMITER}"
SUBSCRIBE_REQUEST = f"{SUBSCRIBE}{DELIMITER}"
UNSUBSCRIBE_REQUEST = f"{UNSUBSCRIBE}{DELIMITER}"

CHAT_MESSAGE = f"MSG{DELIMITER}"
REGISTER_USER = f"REG{DELIMITER}"

OK = f"OK.{DELIMITER}"
ERROR = f"ERR.{DELIMITER}"


def construct_chat_message(message):
    return f"{CHAT_MESSAGE}{message}"


def construct_weather_response(data):
    return f"{WEATHER}{DELIMITER}{data}"


def construct_currency_response(data):
    return f"{CURRENCY}{DELIMITER}{data}"


def register_client_to_server(card: ClientCard):
    """Register a client to the server
    card_data: dict with keys 'name' and 'apartment_no'"""
    return f"{REGISTER_USER}{card.name}{DELIMITER}{card.apartment_no}"


def parse_register_response(data):
    """Parse the response from the server after registering a client"""
    return {'name': data.split(DELIMITER)[1], 'apartment_no': data.split(DELIMITER)[2]}


def strip_delimiter(data):
    return data.split(DELIMITER)[1]
