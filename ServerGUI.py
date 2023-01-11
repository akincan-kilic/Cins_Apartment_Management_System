import multiprocessing
import sys
import threading
import time

import flet as ft
from flet import Row, Column

import AkinProtocol
import Utility
import custom_exceptions as ce
from Server import Server
from ServerController import ServerController

logger = Utility.get_logger()


class ServerGUI:
    server: Server
    WINDOW_HEIGHT = 780
    WINDOW_WIDTH = 800
    APP_NAME = "Cins Apartment Server Admin Panel"

    def __init__(self):
        self.host = AkinProtocol.DEFAULT_HOST
        self.port = AkinProtocol.DEFAULT_PORT
        self.controller = ServerController(host=self.host, port=self.port)

        ### Main Application ###
        self.app_title = ft.Text(value=self.APP_NAME, style=ft.TextThemeStyle.DISPLAY_SMALL, font_family="RobotoSlab",
                                 width=800, text_align=ft.TextAlign.LEFT)
        self.app_icon = ft.Icon(name=ft.icons.ACCESS_ALARM, size=50)
        self.theme_switcher = ft.IconButton(icon=ft.icons.NIGHTLIGHT_OUTLINED, tooltip="Switch Dark/Light Theme",
                                            icon_size=24, on_click=self.__on_click_switch_theme)
        self.exit_button = ft.IconButton(icon=ft.icons.CANCEL_OUTLINED, tooltip="Exit", icon_size=28,
                                         on_click=self.__on_click_exit_button)

        self.fetch_frequency_textbox = ft.TextField(label="Weather and Currency Fetch Frequency (in seconds)",
                                                    value="60", width=200)

        ### Server Controls ###
        self.start_button = ft.ElevatedButton(text="Start Server", on_click=self.__on_click_start_button)
        self.stop_button = ft.ElevatedButton(text="Stop Server", on_click=self.__on_click_stop_button)
        self.msg_list = ft.ListView(expand=1, spacing=10, padding=20)

        self.host_textbox = ft.TextField(label="Host", value=str(self.host), width=200)
        self.port_textbox = ft.TextField(label="Port", value=str(self.port), width=200)

        self.clients_grid_view = ft.GridView(expand=True, max_extent=150, child_aspect_ratio=1)

        self.open_connections_length_text = ft.Text(value="Open Connections: 0", style=ft.TextThemeStyle.BODY_LARGE,
                                                    font_family="RobotoSlab", width=200, text_align=ft.TextAlign.LEFT)
        self.open_connections_list_text = ft.Text(value="", style=ft.TextThemeStyle.BODY_LARGE,
                                                  font_family="RobotoSlab", width=800, text_align=ft.TextAlign.LEFT)

        self.server_status_text = ft.Text(value="Server Status:", style=ft.TextThemeStyle.BODY_LARGE,
                                          font_family="RobotoSlab", width=200, text_align=ft.TextAlign.LEFT)
        self.server_status_online_text = ft.Text(value="Offline", style=ft.TextThemeStyle.BODY_LARGE,
                                                 font_family="RobotoSlab", width=100, text_align=ft.TextAlign.LEFT,
                                                 color=ft.colors.RED)
        self.open_connections_listener = threading.Thread(target=self.list_open_connections, daemon=True).start()
        self.server_log_listener = threading.Thread(target=self.listen_for_messages_from_server_and_update_message_box,
                                                    daemon=True).start()

    # ------------------------ #
    # --- On Click Methods --- #
    # ------------------------ #
    def __on_click_start_button(self, _) -> None:
        """Starts the server."""
        logger.debug("On Click: Start Button")
        self.start_server()

    def __on_click_exit_button(self, _) -> None:
        """Closes the application window."""
        logger.debug("On Click: Exit Button")
        self.page.window_destroy()
        self.stop_server()
        sys.exit(0)

    def __on_click_stop_button(self, _) -> None:
        """Stops the server."""
        logger.debug("On Click: Stop Button")
        self.stop_server()

    def __on_click_switch_theme(self, _) -> None:
        """Switches the theme of the GUI between light and dark."""
        logger.debug("Switching theme...")
        self.page.theme_mode = ft.ThemeMode.LIGHT if self.page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        self.page.update()

    # --------------- #
    # --- Threads --- #
    # --------------- #

    def list_open_connections(self):
        """Listens for open connections and updates the GUI."""
        while True:
            if self.controller.server_running:
                open_connections = self.controller.get_open_connections()
                self.open_connections_list_text.value = self.__parse_open_connections_to_str(open_connections)
                self.open_connections_length_text.value = f"Open Connections: {len(open_connections)}"
            else:
                self.open_connections_list_text.value = ""
                self.open_connections_length_text.value = "Open Connections: 0"
            time.sleep(0.1)

    def listen_for_messages_from_server_and_update_message_box(self) -> None:
        """Listens for messages from the server and updates the GUI message box."""
        server_logs: multiprocessing.Queue = self.controller.logger
        while True:
            if self.controller.server_running and not server_logs.empty():
                msg = server_logs.get()
                self.update_msg_list(msg)
            time.sleep(0.1)

    # ---------------------- #
    # --- Helper Methods --- #
    # ---------------------- #
    def start_server(self):
        self.update_msg_list("Starting server...")
        self.host = str(self.host_textbox.value)
        self.port = int(str(self.port_textbox.value))
        try:
            self.controller.start_server()
        except ce.ServerAlreadyRunningError as e:
            self.update_msg_list("Server is already running.")
            return
        except ce.InvalidPortError as e:
            self.update_msg_list(f"Invalid port. {e}")
            return
        self.__change_server_status_text(online=True)

    def stop_server(self):
        self.update_msg_list("Stopping server...")
        try:
            self.controller.stop_server()
        except ce.ServerNotRunningError as e:
            self.update_msg_list("Server is not running.")
            return
        except ce.ServerCouldNotBeClosedError as e:
            self.update_msg_list(f"Server could not be closed. {e}")
            return
        self.update_msg_list("Server stopped.")
        self.__change_server_status_text(online=False)

    @staticmethod
    def __parse_open_connections_to_str(open_connections):
        out_str = ""
        for idx, connection in enumerate(open_connections):
            out_str += f"{idx}. {connection}\n"
        return out_str

    def __change_server_status_text(self, online: bool) -> None:
        if online:
            self.server_status_online_text.value = "Online"
            self.server_status_online_text.color = ft.colors.GREEN
        else:
            self.server_status_online_text.value = "Offline"
            self.server_status_online_text.color = ft.colors.RED
        self.page.update()

    def __change_fetch_frequency(self, _) -> None:
        self.controller.fetch_frequency = int(self.fetch_frequency_textbox.value)
        # todo

    def update_msg_list(self, message: str) -> None:
        self.msg_list.controls.append(ft.Text(f"{Utility.get_detailed_time()}: {message}"))
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

    def __draw_server_controls(self) -> None:
        self.page.add(Row(controls=[self.host_textbox, self.port_textbox], wrap=False))
        self.page.add(Row(controls=[self.start_button,
                                    self.stop_button,
                                    self.server_status_text,
                                    self.server_status_online_text,
                                    self.fetch_frequency_textbox], wrap=False))

    def __draw_open_connections(self) -> None:
        connections_col1 = Column(controls=[self.open_connections_length_text, self.open_connections_list_text],
                                  wrap=False)
        self.page.add(connections_col1)

    def __draw_message_list(self) -> None:
        self.page.add(self.msg_list)

    def __call__(self, flet_page: ft.Page) -> None:
        """Create the page and add controls to it on call."""
        self.page = flet_page
        self.__init_window()
        self.__draw_app_bar()
        self.__draw_server_controls()
        self.__draw_open_connections()
        self.__draw_message_list()
        self.page.update()


if __name__ == '__main__':
    # view=ft.WEB_BROWSER
    ft.app(target=ServerGUI(), assets_dir="assets")
