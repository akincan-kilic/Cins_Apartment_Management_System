import datetime
import logging
import random


def get_simple_time() -> str:
    """Returns the current time in the format [HH:MM:SS]"""
    return datetime.datetime.now().strftime("%H:%M:%S")


def get_detailed_time() -> str:
    """Returns the current time in the format [DD-MM-YYYY] | [HH:MM:SS]"""
    return datetime.datetime.now().strftime("%d-%m-%Y | %H:%M:%S")


def get_random_card_name() -> str:
    """Returns a random card name from a predefined list."""
    random_card_names = ['Akıncan Kılıç', 'Muhammet Gökhan Erdem', 'Bora Canbula', 'Nane Limon', 'Demli Çay',
                         'Gürültücü Komşu', 'Sessiz Komşu', 'Komşu Köpeği', 'Komşu Kedisi', 'Komşu Kızı']
    return random.choice(random_card_names)


def get_random_card_apartment_no() -> str:
    """Returns a random apartment number between 1 and 1000."""
    return str(random.randint(100, 1000))


def get_logger():
    # Logger configuration.
    logging.basicConfig(
        format="[%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler("trend_scraper.log"),
            logging.StreamHandler()
        ]
    )

    logging.getLogger('flet').setLevel(logging.ERROR)
    logging.getLogger('snscrape').setLevel(logging.ERROR)
    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)
    return logger
