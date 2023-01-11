import multiprocessing
import threading
import time

import flet as ft
from flet import Column, Row

import AkinProtocol
import Utility
import custom_exceptions as ce
from ClientCard import ClientCard
from ClientController import ClientController

logger = Utility.get_logger()


class ClientGUI:
    DEFAULT_CLIENT_NAME = Utility.get_random_card_name()
    DEFAULT_CLIENT_NO = Utility.get_random_card_apartment_no()
    WINDOW_HEIGHT = 780
    WINDOW_WIDTH = 1200
    APP_NAME = "Cins Apartment Resident Client"

    def __init__(self):
        self.white_gradient = ft.LinearGradient(begin=ft.alignment.top_center,
                                                end=ft.alignment.bottom_center,
                                                colors=[ft.colors.WHITE, ft.colors.BLUE_GREY_100])
        self.dark_gradient = ft.LinearGradient(begin=ft.alignment.top_center,
                                               end=ft.alignment.bottom_center,
                                               colors=[ft.colors.BLACK, ft.colors.BLUE_GREY_100])
        ### Server Logic ###
        self.host = AkinProtocol.DEFAULT_HOST
        self.port = AkinProtocol.DEFAULT_PORT
        self.group_chat_message_queue: multiprocessing.Queue = None  # type: ignore
        self.running_flag = True

        ### Main Application ###
        self.app_title = ft.Text(value=self.APP_NAME, style=ft.TextThemeStyle.DISPLAY_SMALL, font_family="RobotoSlab",
                                 width=800, text_align=ft.TextAlign.LEFT)
        self.app_icon = ft.Icon(name=ft.icons.ACCESS_ALARM, size=50)
        self.theme_switcher = ft.IconButton(icon=ft.icons.NIGHTLIGHT_OUTLINED, tooltip="Switch Dark/Light Theme",
                                            icon_size=24, on_click=self.__on_click_switch_theme)
        self.exit_button = ft.IconButton(icon=ft.icons.CANCEL_OUTLINED, tooltip="Exit", icon_size=28,
                                         on_click=self.__on_click_exit_button)

        self.host_textbox = ft.TextField(label="Host", value=str(self.host), width=200)
        self.port_textbox = ft.TextField(label="Port", value=str(self.port), width=200)
        self.start_button = ft.ElevatedButton(text="Connect to Server", on_click=self.__on_click_start_button)
        self.close_connection_button = ft.ElevatedButton(text="Disconnect from Server",
                                                         on_click=self.__on_click_close_connection_button,
                                                         disabled=True)

        self.client_card_image = ft.Image(src='CinsApartmentCard_Transparent.png')
        self.client_card_name = ft.TextField(label="Client Name", value=self.DEFAULT_CLIENT_NAME, width=200)
        self.client_card_no = ft.TextField(label="Client Apartment No", value=str(self.DEFAULT_CLIENT_NO), width=200)
        self.register_client_button = ft.ElevatedButton(text="Register Client by Scanning Their Card on the Reader",
                                                        on_click=self.__on_click_register_client_button)
        self.client_card = self.__generate_client_card()

        self.msg_list = ft.ListView(expand=1, spacing=10, padding=20)
        self.message_input_field = ft.TextField(label="Enter a message to send...", value="", disabled=True, width=500)
        self.send_message_button = ft.IconButton(icon=ft.icons.SEND, on_click=self.__on_click_message_send_button)
        self.subscribe_to_messages_button = ft.ElevatedButton(text="Subscribe to Messages",
                                                              on_click=self.__on_click_subscribe_to_messages_button)

        self.controller = ClientController(host=self.host,
                                           port=self.port)

        ### Weather Display ###
        self.weather_text = ft.Text(value="Weather from Server", style=ft.TextThemeStyle.LABEL_MEDIUM,
                                    font_family="RobotoSlab", width=800, text_align=ft.TextAlign.CENTER)
        self.weather_container = Utility.get_info_container()
        self.weather_image = ft.Image(src='weather.png', width=50, height=50)
        self.wind_image = ft.Image(src='wind.png', width=50, height=50)
        self.weather_in_celcius_text = ft.Text(value="0.0 °C",
                                               style=ft.TextThemeStyle.LABEL_LARGE,
                                               font_family="RobotoSlab",
                                               width=200,
                                               text_align=ft.TextAlign.LEFT)
        self.wind_details_text = ft.Text(value="0 m/s, 0°",
                                         style=ft.TextThemeStyle.LABEL_LARGE,
                                         font_family="RobotoSlab",
                                         width=200,
                                         text_align=ft.TextAlign.LEFT)
        self.weather_row = Row([self.weather_image, self.weather_in_celcius_text])
        self.wind_row = Row([self.wind_image, self.wind_details_text])
        self.weather_column = Column(controls=[self.weather_text, self.weather_row, self.wind_row], wrap=False)
        self.weather_container.content = self.weather_column

        ### Currency Display ###
        self.currency_text = ft.Text(value="Currency from Server", style=ft.TextThemeStyle.LABEL_MEDIUM,
                                     font_family="RobotoSlab", width=800, text_align=ft.TextAlign.CENTER)
        self.currency_container = Utility.get_info_container()
        self.euro_image = ft.Image(src='euro.png', width=50, height=50)
        self.dollar_image = ft.Image(src='dollar.png', width=50, height=50)
        self.euro_text = ft.Text(value="0 €",
                                 style=ft.TextThemeStyle.LABEL_LARGE,
                                 font_family="RobotoSlab",
                                 width=200,
                                 text_align=ft.TextAlign.LEFT)
        self.dollar_text = ft.Text(value="0 $",
                                   style=ft.TextThemeStyle.LABEL_LARGE,
                                   font_family="RobotoSlab",
                                   width=200,
                                   text_align=ft.TextAlign.LEFT)
        self.euro_row = Row([self.euro_image, self.euro_text])
        self.dollar_row = Row([self.dollar_image, self.dollar_text])
        self.currency_column = Column(controls=[self.currency_text, self.euro_row, self.dollar_row], wrap=False)
        self.currency_container.content = self.currency_column

        self.chat_box_container = ft.Container(content=self.msg_list,
                                               ink=True,
                                               width=500,
                                               height=400,
                                               border_radius=ft.border_radius.all(20),
                                               border=ft.border.all(4, ft.colors.BLACK),
                                               padding=ft.padding.all(10),
                                               gradient=self.white_gradient)
        self.__start_helper_threads()

    # ------------------------ #
    # --- On Click Methods --- #
    # ------------------------ #
    def __on_click_register_client_button(self, _) -> None:
        """Registers a client."""
        logger.debug("On Click: Register Client Button")
        try:
            self.client_card = self.__generate_client_card()
            self.controller.register_client(self.client_card)
            self.register_client_button.disabled = True
            self.register_client_button.text = "Client has been successfully registered by the Server!"
            Utility.create_snackbar(self.page,
                                    f"Client registered under name: {self.client_card.name} and apartment no: {self.client_card.apartment_no}")
        except Exception as e:
            Utility.create_snackbar(self.page, f"Could not register the client. Reason: {e}")
            logger.exception(e.with_traceback(e.__traceback__))

    def __on_click_subscribe_to_messages_button(self, _) -> None:
        """Subscribes to the server."""
        logger.debug("On Click: Subscribe Button")
        if not self.controller.client_running:
            Utility.create_snackbar(self.page, "The client is not running.")
            return
        self.group_chat_message_queue = self.controller.get_message_queue()
        if self.subscribe_to_messages_button.text == "Unsubscribe from Messages":
            try:
                self.controller.unsubscribe_from_message_channel()
            except ce.ClientNotRunningError:
                Utility.create_snackbar(self.page, "The client is not running.")
                return
            self.__toggle_subscribe_button_action(
                True,
                "Subscribe to Messages",
                "Unsubscribed from the apartment group chat.",
            )
        elif self.subscribe_to_messages_button.text == "Subscribe to Messages":
            try:
                self.controller.subscribe_to_message_channel()
            except ce.ClientNotRunningError:
                Utility.create_snackbar(self.page, "The client is not running.")
                return
            self.__toggle_subscribe_button_action(
                False,
                "Unsubscribe from Messages",
                "Subscribed to the apartment group chat.",
            )
        self.page.update()

    def __on_click_close_connection_button(self, _) -> None:
        """Closes the connection to the server."""
        logger.debug("On Click: Close Connection Button")
        self.start_button.disabled = False
        self.start_button.text = "Connect to Server"
        self.controller.stop_client()
        self.running_flag = False
        self.page.update()

    def __on_click_message_send_button(self, _) -> None:
        """Sends a message to the server."""
        logger.debug("On Click: Message Send Button")
        user_message = str(self.message_input_field.value)
        self.message_input_field.value = ""
        self.controller.send_message(user_message)
        self.page.update()

    def __on_click_start_button(self, _) -> None:
        """Starts the server."""
        try:
            logger.debug("On Click: Start Button")
            self.host = str(self.host_textbox.value)
            self.port = int(str(self.port_textbox.value))
            self.controller.start_client(self.host, self.port)
            self.start_button.text = "Connected to Server!"
            self.start_button.disabled = True
            self.close_connection_button.disabled = False
            self.page.update()
        except Exception as e:
            Utility.create_snackbar(self.page, f"An error occurred: {e}")

    def __on_click_exit_button(self, _) -> None:
        """Closes the application window."""
        logger.debug("On Click: Exit Button")
        self.running_flag = False
        self.page.window_destroy()

    def __on_click_switch_theme(self, _) -> None:
        """Switches the theme of the GUI between light and dark."""
        logger.debug("Switching theme...")
        self.page.theme_mode = ft.ThemeMode.LIGHT if self.page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        self.client_card_image.src = 'CinsApartmentCard_Transparent_White.png' if self.page.theme_mode == ft.ThemeMode.DARK else 'CinsApartmentCard_Transparent.png'
        self.chat_box_container.gradient = self.dark_gradient if self.page.theme_mode == ft.ThemeMode.DARK else self.white_gradient
        self.page.update()

    # --------------- #
    # --- Threads --- #
    # --------------- #
    def __start_helper_threads(self):
        """Called after the initialization of the application."""
        threading.Thread(target=self.__update_weather_and_currency).start()
        threading.Thread(target=self.__update_group_chat).start()

    def __update_weather_and_currency(self) -> None:
        """Run this function every second on a separate thread to update the weather and currency information."""
        while self.running_flag:
            # logger.debug("Updating weather and currency information...")
            try:
                weather_data = self.controller.get_weather()
                currency_data = self.controller.get_currency()
                self.__update_weather(weather_data)
                self.__update_currency(currency_data)
            except ce.ClientNotRunningError:
                pass
            time.sleep(1)

    def __update_group_chat(self) -> None:
        """Run this function every second on a separate thread to update the group chat."""
        while self.running_flag:
            if self.controller.client_running:
                # logger.debug("Updating group chat...")
                if self.group_chat_message_queue is None:
                    self.group_chat_message_queue = self.controller.get_message_queue()
                if not self.group_chat_message_queue.empty():
                    message = self.group_chat_message_queue.get()
                    logger.debug(f"New message in the group chat message queue. Message: {message}")
                    self.__update_msg_list(message)
            time.sleep(1)

    # ---------------------- #
    # --- Helper Methods --- #
    # ---------------------- #
    def __update_weather(self, weather: dict) -> None:
        """Update the weather information on the GUI."""
        # logger.debug(f"Updating weather information: {weather}")
        self.weather_in_celcius_text.value = f"{weather['temperature']:.1f} °C"
        self.wind_details_text.value = f"{weather['wind_speed']}m/s {weather['wind_direction']}°"
        self.page.update()

    def __update_currency(self, currency: dict) -> None:
        """Update the currency information on the GUI."""
        # logger.debug(f"Updating currency information: {currency}")
        self.dollar_text.value = f"{currency['usd']}$"
        self.euro_text.value = f"{currency['eur']}€"
        self.page.update()

    def __generate_client_card(self) -> ClientCard:
        """Generates a client card."""
        return ClientCard(str(self.client_card_name.value), int(str(self.client_card_no.value)))

    def __toggle_subscribe_button_action(self, disable_inputs_bool, button_text, snackbar_message):
        self.message_input_field.disabled = disable_inputs_bool
        self.send_message_button.disabled = disable_inputs_bool
        self.subscribe_to_messages_button.text = button_text
        Utility.create_snackbar(self.page, snackbar_message)

    def __update_msg_list(self, message: str) -> None:
        self.msg_list.controls.append(ft.Text(f"{message}"))
        self.page.update()

    # ------------------- #
    # --- GUI Drawing --- #
    # ------------------- #
    def __init_window(self) -> None:
        """Initializes the window of the GUI."""
        self.page = Utility.initialize_flet_gui_page(page=self.page,
                                                     title=self.APP_NAME,
                                                     window_width=self.WINDOW_WIDTH,
                                                     window_height=self.WINDOW_HEIGHT)

    def __draw_app_bar(self) -> None:
        """Add the app bar on the page."""
        self.page.appbar = ft.AppBar(leading=self.app_icon,
                                     leading_width=48,
                                     title=self.app_title,
                                     center_title=False,
                                     actions=[self.theme_switcher, self.exit_button])

    def __call__(self, flet_page: ft.Page) -> None:
        """Create the page and add controls to it on call."""
        self.page = flet_page
        self.__init_window()
        self.__draw_app_bar()
        info_column = Row(controls=[self.weather_container, self.currency_container], wrap=False)
        host_port_row = Row(controls=[self.host_textbox, self.port_textbox], wrap=False)
        client_buttons_row = Row(
            controls=[self.subscribe_to_messages_button, self.start_button, self.close_connection_button], wrap=False,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY)
        host_port_connection_row = Column(controls=[host_port_row, client_buttons_row], wrap=False)

        message_box_row = Row(controls=[self.message_input_field, self.send_message_button], wrap=False)
        host_port_connection_chat_column = Column(
            controls=[host_port_connection_row, self.chat_box_container, message_box_row], wrap=False)
        card_name_no_row = Row(controls=[self.client_card_name, self.client_card_no], wrap=False)
        client_card_column = Column(controls=[self.client_card_image, card_name_no_row], wrap=False)
        info_with_client_card_column = Column(controls=[client_card_column, info_column, self.register_client_button],
                                              wrap=False)

        left_of_page_container = ft.Container(width=self.page.window_width / 2 - 30,  # type: ignore
                                              height=self.page.window_height,
                                              border_radius=ft.border_radius.all(20),
                                              padding=ft.padding.all(10))

        right_of_page_container = ft.Container(width=self.page.window_width / 2 - 30,  # type: ignore
                                               height=self.page.window_height,
                                               border_radius=ft.border_radius.all(20),
                                               padding=ft.padding.all(10))

        left_of_page_container.content = host_port_connection_chat_column
        right_of_page_container.content = info_with_client_card_column
        self.page.add(Row(controls=[left_of_page_container, ft.VerticalDivider(), right_of_page_container], wrap=False))
        self.page.update()


if __name__ == '__main__':
    # view=ft.WEB_BROWSER
    ft.app(target=ClientGUI(), assets_dir="assets")
