import datetime
import logging
import random

import flet as ft

START_BUTTON_STYLE = ft.ButtonStyle(
    color={
        ft.MaterialState.DEFAULT: ft.colors.WHITE,
        ft.MaterialState.DISABLED: ft.colors.BLUE_GREY_100,
    },
    bgcolor={
        ft.MaterialState.HOVERED: ft.colors.LIGHT_GREEN_600,
        ft.MaterialState.DEFAULT: ft.colors.LIGHT_GREEN_800,
        ft.MaterialState.DISABLED: ft.colors.BLUE_GREY_900,
    })

CLIENT_BUTTON_STYLE = ft.ButtonStyle(
    color={
        ft.MaterialState.DEFAULT: ft.colors.AMBER_ACCENT,
        ft.MaterialState.DISABLED: ft.colors.BLUE_GREY_100,
        ft.MaterialState.PRESSED: ft.colors.WHITE,
    },
    bgcolor={
        ft.MaterialState.DEFAULT: ft.colors.PURPLE_600,
        ft.MaterialState.DISABLED: ft.colors.BLUE_GREY_900,
        ft.MaterialState.PRESSED: ft.colors.RED_400,
    },
    shape=ft.BeveledRectangleBorder(radius=10))


def get_flet_exit_button() -> ft.IconButton:
    return ft.IconButton(icon=ft.icons.CANCEL_OUTLINED,
                         tooltip="Exit",
                         icon_size=28,
                         icon_color=ft.colors.RED_400)


def get_flet_theme_switch_button() -> ft.IconButton:
    return ft.IconButton(icon=ft.icons.NIGHTLIGHT_OUTLINED,
                         tooltip="Switch Dark/Light Theme",
                         icon_size=24)


def get_flet_app_title(app_name: str) -> ft.Text:
    return ft.Text(value=app_name,
                   style=ft.TextThemeStyle.DISPLAY_SMALL,
                   font_family="RobotoSlab",
                   width=800,
                   text_align=ft.TextAlign.LEFT)


def get_simple_time() -> str:
    """Returns the current time in the format [HH:MM:SS]"""
    return datetime.datetime.now().strftime("%H:%M:%S")


def get_detailed_time() -> str:
    """Returns the current time in the format [DD-MM-YYYY] | [HH:MM:SS]"""
    return datetime.datetime.now().strftime("%d-%m-%Y | %H:%M:%S")


def get_random_card_name() -> str:
    """Returns a random card name from a predefined list."""
    random_card_names = ['Akıncan Kılıç', 'Muhammet Gökhan Erdem', 'Bora Canbula', 'Nane Limon', 'Demli Çay',
                         'Gürültücü Komşu', 'Sessiz Komşu', 'Komşu Köpeği', 'Komşu Kedisi', 'Komşu Kızı', ]
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


def initialize_flet_gui_page(page: ft.Page, title: str, window_height: int, window_width: int) -> ft.Page:
    """Initializes the given page with the given parameters."""
    page.title = title
    page.window_height = window_height
    page.window_width = window_width
    page.window_title_bar_hidden = False
    page.window_frameless = False
    page.window_always_on_top = False
    page.window_focused = True
    page.window_center()
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {"RobotoSlab": "https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf"}

    return page


def create_snackbar(page: ft.Page, message: str) -> None:
    """Creates a snackbar with the given message and displays it."""
    sb = ft.SnackBar(content=ft.Text(message), action='OK', action_color=ft.colors.GREEN,
                     )
    sb.open = True
    page.add(sb)
    page.update()


def get_info_container(rows_of_items: int) -> ft.Container:
    return ft.Container(width=200,
                        height=100 + (rows_of_items * 50),
                        padding=ft.padding.all(10),
                        margin=ft.margin.all(10),
                        border=ft.border.all(1),
                        border_radius=10,
                        alignment=ft.alignment.top_right)


def get_container_text(text_value: str) -> ft.Text:
    return ft.Text(value=text_value,
                   style=ft.TextThemeStyle.LABEL_LARGE,
                   font_family="RobotoSlab",
                   width=200,
                   text_align=ft.TextAlign.LEFT)
