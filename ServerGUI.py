import flet as ft
import asyncio
import time
import datetime

from flet import Row, Column
import logging

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

class ServerGUI:
    """GUI for the Tweet Classifier App."""
    def __init__(self, host: str, port: int):
        ### Server Logic ###
        self.host = host
        self.port = port
        self.server: asyncio.AbstractServer = None

        ### CONSTANTS ###
        self.APP_NAME = "Cins Apartment Server"

        ### Main Application ###
        self.app_title = ft.Text(value=self.APP_NAME, style="displaySmall", font_family="RobotoSlab", width=800, text_align="left", color=ft.colors)
        self.app_icon = ft.Icon(name=ft.icons.ACCESS_ALARM, size=50)
        self.theme_switcher = ft.IconButton(icon=ft.icons.NIGHTLIGHT_OUTLINED, tooltip="Switch Dark/Light Theme", icon_size=24, on_click=self.__switch_theme)
        self.exit_button = ft.IconButton(icon=ft.icons.CANCEL_OUTLINED, tooltip="Exit", icon_size=28, on_click=self.__on_click_exit_button)

        self.start_button = ft.ElevatedButton(text="Start Server", on_click=self.__on_click_start_button)
        self.msg_list = ft.ListView(expand=1, spacing=10, padding=20)

    async def start(self):
        self.update_msg_list("Starting server...")
        self.server = await asyncio.start_server(self.accept_connection, self.host, self.port) # Start the server.
        self.update_msg_list("Server successfully started.")
        await self.server.serve_forever() # This will block this thread until the server is stopped.

        logger.info("Server stopped.")
        self.update_msg_list("Server stopped.")

    async def accept_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        logger.info("Accepted connection from:", writer.get_extra_info("peername"))
        self.update_msg_list(f"Accepted connection from: {writer.get_extra_info('peername')}")
        while True:
            data = await reader.read(1024)
            if not data:
                break
            await self.receive_data(data, writer)
        writer.close()

    async def receive_data(self, data: bytes, writer: asyncio.StreamWriter) -> None:
        message_received = data.decode()
        logger.info("Received data:", message_received)
        self.update_msg_list(f"Received data: {message_received}")
        writer.write(data) # Echo the data back to the client.

    def update_msg_list(self, message: str) -> None:
        self.msg_list.controls.append(ft.Text(f"{self.get_time()}: {message}"))
        self.page.update()

    def get_time(self) -> str:
        """Returns the current time in the format [DD-MM-YYYY] | [HH:MM:SS]"""
        return datetime.datetime.now().strftime("%d-%m-%Y | %H:%M:%S")

    def __on_click_start_button(self, _) -> None:
        """Starts the server."""
        logger.debug("On Click: Start Button")
        asyncio.run(self.start())

    def __on_click_exit_button(self, _) -> None:
        """Closes the application window."""
        logger.debug("On Click: Exit Button")
        self.page.window_destroy()

    def __create_snackbar(self, message: str) -> None:
        """Creates a snackbar with the given message and displays it."""
        logger.debug(f"Creating a snackbar with message: {message}")
        sb = ft.SnackBar(content=ft.Text(message), action='OK', action_color=ft.colors.WHITE)
        sb.open = True
        self.page.add(sb)
        self.page.update()

    def __init_window(self) -> None:
        """Initializes the window of the GUI."""
        self.page.window_height = 780
        self.page.window_width = 800
        self.page.window_title_bar_hidden = False
        self.page.window_frameless = False
        self.page.window_always_on_top = False
        self.page.window_focused = True
        self.page.window_center()
        self.page.theme_mode = "light"
        self.page.title = self.APP_NAME

    def __switch_theme(self, _) -> None:
        """Switches the theme of the GUI between light and dark."""
        logger.debug("Switching theme...")
        self.page.theme_mode = "light" if self.page.theme_mode == "dark" else "dark"
        self.page.update()

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
        self.page.fonts = {"RobotoSlab": "https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf"}
        self.__init_window()
        self.__draw_app_bar()
        self.page.add(self.start_button)
        self.page.add(self.msg_list)
        self.page.update()


if __name__ == '__main__':
    # view=ft.WEB_BROWSER
    ft.app(target=ServerGUI("localhost", 5000), assets_dir="assets")