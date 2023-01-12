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
    WINDOW_HEIGHT = 820
    WINDOW_WIDTH = 1200
    APP_NAME = "Cins Apartment Client"
    SUBSCRIBE_BUTTON_TEXT = "Join to the Apartment Group Chat"
    UNSUBSCRIBE_BUTTON_TEXT = "Leave the Apartment Group Chat"

    def __init__(self):
        self.white_gradient = ft.LinearGradient(begin=ft.alignment.top_center,
                                                end=ft.alignment.bottom_center,
                                                colors=[ft.colors.PURPLE_100, ft.colors.BLUE_GREY_100])
        self.dark_gradient = ft.LinearGradient(begin=ft.alignment.top_center,
                                               end=ft.alignment.bottom_center,
                                               colors=[ft.colors.BLACK, ft.colors.PINK_200])
        ### Server Logic ###
        self.host = AkinProtocol.DEFAULT_HOST
        self.port = AkinProtocol.DEFAULT_PORT
        self.group_chat_message_queue: multiprocessing.Queue = None  # type: ignore
        self.running_flag = True
        self.client_registered = False

        ### Main Application ###
        self.app_title = Utility.get_flet_app_title(self.APP_NAME)
        self.app_icon = ft.Image('client.png', width=96, height=96)

        self.theme_switcher = Utility.get_flet_theme_switch_button()
        self.theme_switcher.on_click = self.__on_click_switch_theme

        self.exit_button = Utility.get_flet_exit_button()
        self.exit_button.on_click = self.__on_click_exit_button

        self.host_textbox = ft.TextField(label="Host", value=str(self.host), width=200)
        self.port_textbox = ft.TextField(label="Port", value=str(self.port), width=120)
        self.start_button = ft.ElevatedButton(text="Connect to Server",
                                              on_click=self.__on_click_start_button,
                                              style=Utility.START_BUTTON_STYLE)

        self.client_card_image = ft.Image(src='CinsApartmentCard_Transparent.png')
        self.client_card_name = ft.TextField(label="Name",
                                             value=self.DEFAULT_CLIENT_NAME,
                                             width=280)

        self.client_card_no = ft.TextField(label="Apartment No",
                                           value=str(self.DEFAULT_CLIENT_NO),
                                           width=120)
        self.register_client_button = ft.ElevatedButton(text="Register Client by Scanning Their Card on the Reader",
                                                        on_click=self.__on_click_register_client_button,
                                                        style=Utility.CLIENT_BUTTON_STYLE)
        self.client_card = self.__generate_client_card()

        self.msg_list = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
        self.message_input_field = ft.TextField(label="Enter a message to send...", value="", disabled=True, width=500)
        self.send_message_button = ft.IconButton(icon=ft.icons.SEND, on_click=self.__on_click_message_send_button)
        self.subscribe_to_messages_button = ft.ElevatedButton(text=self.SUBSCRIBE_BUTTON_TEXT,
                                                              on_click=self.__on_click_subscribe_to_messages_button,
                                                              style=Utility.CLIENT_BUTTON_STYLE)

        self.controller = ClientController(host=self.host,
                                           port=self.port)

        ### Weather Display ###
        self.weather_description_text = Utility.get_container_text("Weather Description")
        self.temperature_celcius_text = Utility.get_container_text("0°C")
        self.day_temperature_celcius_text = Utility.get_container_text("0°C")
        self.night_temperature_celcius_text = Utility.get_container_text("0°C")

        ### Currency Display ###

        self.euro_text = Utility.get_container_text("0₺")
        self.dollar_text = Utility.get_container_text("0₺")
        self.sterling_text = Utility.get_container_text("0₺")
        self.bitcoin_text = Utility.get_container_text("0₺")
        self.gold_text = Utility.get_container_text("0₺")

        ### MSG BOX ###
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
            self.client_registered = True
            self.register_client_button.text = "Client has been successfully registered by the Server!"
            Utility.create_snackbar(self.page, f"Client registered under name: {self.client_card.name} and apartment no: {self.client_card.apartment_no}")
        except Exception as e:
            Utility.create_snackbar(self.page, f"Could not register the client. Reason: {e}")
            logger.exception(e.with_traceback(e.__traceback__))

    def __on_click_subscribe_to_messages_button(self, _) -> None:
        """Subscribes to the server."""
        logger.debug("On Click: Subscribe Button")
        if not self.controller.client_running:
            Utility.create_snackbar(self.page, "The client is not running.")
            return
        if not self.client_registered:
            Utility.create_snackbar(self.page, "Please first register yourself by scanning your card to the card reader.")
            return
        self.group_chat_message_queue = self.controller.get_message_queue()
        if self.subscribe_to_messages_button.text == self.UNSUBSCRIBE_BUTTON_TEXT:
            try:
                self.controller.unsubscribe_from_message_channel()
            except ce.ClientNotRunningError:
                Utility.create_snackbar(self.page, "The client is not running.")
                return
            self.__toggle_subscribe_button_action(
                True,
                self.SUBSCRIBE_BUTTON_TEXT,
                "You just left the apartment group chat...",
            )
        elif self.subscribe_to_messages_button.text == self.SUBSCRIBE_BUTTON_TEXT:
            try:
                self.controller.subscribe_to_message_channel()
            except ce.ClientNotRunningError:
                Utility.create_snackbar(self.page, "The client is not running.")
                return
            self.__toggle_subscribe_button_action(
                False,
                self.UNSUBSCRIBE_BUTTON_TEXT,
                "You just joined to the apartment group chat!",
            )
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
        logger.debug("On Click: Start Button")
        try:
            if not self.port_textbox.value.isdigit():
                raise ValueError("Port must be an integer.")

            self.host = str(self.host_textbox.value)
            self.port = int(str(self.port_textbox.value))

            self.start_button.text = "Trying to connect..."
            self.start_button.disabled = True
            self.page.update()

            self.controller.start_client(self.host, self.port)
            self.start_button.text = "Connected!"
            self.start_button.disabled = True
            self.host_textbox.disabled = True
            self.port_textbox.disabled = True
            self.page.update()
        except ce.NoServersFoundOnThisHostAndPortError as e:
            self.start_button.text = "Connect to Server"
            self.start_button.disabled = False
            self.page.update()
            Utility.create_snackbar(self.page, f"An error occurred: {e}")
        finally:
            self.page.update()

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
        weather_description = weather["weather_description"]
        temp_celcius = weather["temperature_celcius"]
        day_temp_celcius = weather["day_temp_celcius"]
        night_temp_celcius = weather["night_temp_celcius"]

        self.weather_description_text.value = weather_description
        self.temperature_celcius_text.value = f"{temp_celcius}°C"
        self.day_temperature_celcius_text.value = f"{day_temp_celcius}°C"
        self.night_temperature_celcius_text.value = f"{night_temp_celcius}°C"
        self.page.update()

    def __update_currency(self, currency: dict) -> None:
        """Update the currency information on the GUI."""
        # Get upto 4 decimal places

        usd = currency["USD"]
        eur = currency["EUR"]
        sterling = currency["GBP"]
        bitcoin = currency["BTC"]
        gold = currency["GOLD_GR"]

        self.dollar_text.value = f"{usd}₺"
        self.euro_text.value = f"{eur}₺"
        self.sterling_text.value = f"{sterling}₺"
        self.bitcoin_text.value = f"{bitcoin}₺"
        self.gold_text.value = f"{gold}₺ (1GR)"
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

    def __get_weather_container(self):
        weather_container = Utility.get_info_container(rows_of_items=3)

        weather_component_title_text = ft.Text(value="Weather from Server",
                                               style=ft.TextThemeStyle.LABEL_MEDIUM,
                                               font_family="RobotoSlab",
                                               width=800,
                                               text_align=ft.TextAlign.CENTER)

        temp_celcius_image = ft.Image(src='weather.png', width=50, height=50)
        day_temp_image = ft.Image(src='sunrise_v1.png', width=50, height=50)
        night_temp_image = ft.Image(src='night.png', width=50, height=50)

        temperature_row = Row([temp_celcius_image, self.temperature_celcius_text])
        day_temperature_row = Row([day_temp_image, self.day_temperature_celcius_text])
        night_temperature_row = Row([night_temp_image, self.night_temperature_celcius_text])

        weather_column = Column(controls=[weather_component_title_text,
                                          temperature_row,
                                          day_temperature_row,
                                          night_temperature_row,
                                          self.weather_description_text],
                                wrap=False)
        weather_container.content = weather_column
        return weather_container

    def __get_currency_container(self):
        currency_container = Utility.get_info_container(rows_of_items=5)

        dollar_image = ft.Image(src='dollar.png', width=50, height=50)
        euro_image = ft.Image(src='euro.png', width=50, height=50)
        sterling_image = ft.Image(src='sterling.png', width=50, height=50)
        bitcoin_image = ft.Image(src='bitcoin.png', width=50, height=50)
        gold_image = ft.Image(src='gold.png', width=50, height=50)

        ### Currency Display ###
        currency_component_title_text = ft.Text(value="Currency from Server",
                                                style=ft.TextThemeStyle.LABEL_MEDIUM,
                                                font_family="RobotoSlab",
                                                width=800,
                                                text_align=ft.TextAlign.CENTER)

        dollar_row = Row([dollar_image, self.dollar_text])
        euro_row = Row([euro_image, self.euro_text])
        sterling_row = Row([sterling_image, self.sterling_text])
        gold_row = Row([gold_image, self.gold_text])
        bitcoin_row = Row([bitcoin_image, self.bitcoin_text])

        currency_column = Column(controls=[currency_component_title_text,
                                           dollar_row,
                                           euro_row,
                                           sterling_row,
                                           bitcoin_row,
                                           gold_row], wrap=False)

        currency_container.content = currency_column
        return currency_container

    def __draw_host_port_connect_section(self) -> None:
        pass

    def __call__(self, flet_page: ft.Page) -> None:
        """Create the page and add controls to it on call."""
        self.page = flet_page
        self.__init_window()
        self.__draw_app_bar()
        host_port_row = Row(controls=[self.host_textbox,
                                      self.port_textbox,
                                      self.start_button],
                            wrap=False)
        weather_and_currency = Row(controls=[self.__get_weather_container(),
                                             self.__get_currency_container()],
                                   wrap=False)
        message_box_row = Row(controls=[self.message_input_field,
                                        self.send_message_button],
                              wrap=False)

        host_port_connection_chat_column = Column(
            controls=[host_port_row,
                      self.chat_box_container,
                      message_box_row,
                      self.subscribe_to_messages_button],
            wrap=False,
            alignment=ft.MainAxisAlignment.START)

        card_name_no_row = Row(controls=[self.client_card_name,
                                         self.client_card_no],
                               wrap=False)
        client_card_column = Column(controls=[self.client_card_image,
                                              card_name_no_row],
                                    wrap=False)
        info_with_client_card_column = Column(
            controls=[client_card_column,
                      self.register_client_button,
                      weather_and_currency],
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
