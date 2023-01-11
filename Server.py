import multiprocessing
import socket
import sys
import threading
import time

import AkinProtocol
import Utility
import custom_exceptions as ce
from ClientCard import ClientCard
from Currency import CurrencyDataFetcher
from Weather import WeatherDataFetcherAPI


class Server(threading.Thread):
    """A threaded server that handles multiple clients"""

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.running_flag = True
        self.msg_queue = multiprocessing.Queue()
        self.logger = multiprocessing.Queue()
        self.open_connection_threads: list[ClientThread] = []
        self.server_management_thread = ServerManagementThread(self)
        self.weather_data_fetcher = WeatherDataFetcherAPI()
        self.currency_data_fetcher = CurrencyDataFetcher()
        self.group_chat_updater_thread = threading.Thread(target=self.__update_group_chat)
        self.group_chat_updater_thread.start()
        self.weather = AkinProtocol.DEFAULT_WEATHER_DICT
        self.currency = AkinProtocol.DEFAULT_CURRENCY_DICT

    def run(self):
        self.__bind_and_listen()
        self.server_management_thread.start()  # Start a thread to check for closed connections
        while self.running_flag:
            try:
                self.__accept_client_to_a_new_thread()
            except ConnectionAbortedError:
                break  # Server is closed
        sys.exit(0)

    def stop_server(self):
        """Stops the server"""
        self.running_flag = False
        self.server_socket.close()
        for client in self.open_connection_threads:
            client.close_connection()
        sys.exit(0)

    def __bind_and_listen(self):
        """Binds the server to the given host and port and starts listening for connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.running_flag = True
            self.logger.put(f"Server successfully started on [{self.host}:{self.port}]")
            self.logger.put("Waiting for a connection...")
        except socket.error as e:
            raise ce.InvalidPortError(f"Error binding to port {self.port}: {e}") from e

    def __accept_client_to_a_new_thread(self):
        """Accepts a client connection and starts a new thread to handle it"""
        (client_socket, address) = self.server_socket.accept()
        self.logger.put(f"Accepted connection from: {address}, started a new thread to handle this client.")
        client_thread = ClientThread(client_socket, address, self.msg_queue, self.weather, self.currency, self.logger)
        client_thread.start()
        self.open_connection_threads.append(client_thread)

    def __update_group_chat(self):
        while self.running_flag:
            if not self.msg_queue.empty():
                msg = self.msg_queue.get()
                for client in self.open_connection_threads:
                    if client.subscribed_to_message_channel:
                        client.client_socket.send(msg.encode())
            time.sleep(0.1)

    def update_weather(self) -> None:
        """Updates the weather data from the weather data fetcher and returns the weather data"""
        weather = self.weather_data_fetcher.get_manisa_weather_data()
        self.weather = weather

    def update_currency(self) -> None:
        """Updates the currency data from the currency data fetcher and returns the currency data"""
        currency = self.currency_data_fetcher.fetch_exchange_rates()
        self.currency = currency

    def get_weather(self) -> dict:
        return self.weather

    def get_currency(self) -> dict:
        return self.currency


class ClientThread(threading.Thread):
    """A thread that handles a single client connection"""

    def __init__(self, client_socket: socket.socket, client_address, msg_queue: multiprocessing.Queue, weather: dict,
                 currency: dict, logger: multiprocessing.Queue):
        super().__init__()
        self.client_socket = client_socket
        self.client_address = client_address
        self.message_queue = msg_queue
        self.weather = weather
        self.currency = currency
        self.card: ClientCard = None  # type: ignore
        self.subscribed_to_message_channel = False
        self.connection_open_flag = False

    def run(self) -> None:
        """Handle a client connection"""
        self.connection_open_flag = True
        self.client_socket.send(f"Welcome to the server! {self.client_socket.getpeername()}".encode())
        while self.connection_open_flag:
            try:
                client_msg = self.client_socket.recv(1024).decode()
            except ConnectionResetError:
                self.connection_open_flag = False
                break
            self.__handle_client_message(client_msg=client_msg)
        sys.exit(0)

    def update_weather(self, weather: dict) -> None:
        """Updates the weather data that the client will receive when requested"""
        self.weather = weather

    def update_currency(self, currency: dict) -> None:
        """Updates the currency data that the client will receive when requested"""
        self.currency = currency

    def is_connection_open(self) -> bool:
        return self.connection_open_flag

    def close_connection(self) -> None:
        self.connection_open_flag = False
        self.client_socket.close()

    def __handle_client_message(self, client_msg: str) -> None:
        if client_msg.startswith(AkinProtocol.REGISTER_USER):
            self.__handle_register_user(client_msg)

        elif client_msg == AkinProtocol.WEATHER_GET:
            self.__handle_get_weather(client_msg)

        elif client_msg == AkinProtocol.CURRENCY_GET:
            self.__handle_get_currency(client_msg)

        elif client_msg == AkinProtocol.SUBSCRIBE_REQUEST:
            self.__handle_subscribe_request(client_msg)

        elif client_msg == AkinProtocol.UNSUBSCRIBE_REQUEST:
            self.__handle_unsubscribe_request(client_msg)

        elif client_msg.startswith(AkinProtocol.CHAT_MESSAGE):
            self.__handle_chat_message(client_msg)

        else:
            error_message = f"Unknown command: {client_msg}"
            try:
                self.client_socket.send(error_message.encode())
            except BrokenPipeError:
                self.connection_open_flag = False

    def __handle_register_user(self, client_msg: str) -> None:
        """Handles the register user command"""
        card_details = AkinProtocol.parse_register_response(client_msg)
        self.card = ClientCard(card_details['name'], int(card_details['apartment_no']))
        self.client_socket.send(self.card.id.encode())

    def __handle_subscribe_request(self, client_msg: str) -> None:
        """Handles the subscribe request command, this will add the client to the message channel"""
        self.subscribed_to_message_channel = True
        self.client_socket.send(AkinProtocol.OK.encode())

    def __handle_unsubscribe_request(self, client_msg: str) -> None:
        """Handles the unsubscribe request command, this will remove the client from the message channel"""
        self.subscribed_to_message_channel = False
        self.client_socket.send(AkinProtocol.OK.encode())

    def __handle_chat_message(self, client_msg: str) -> None:
        if self.card is None:
            error_message = f"{AkinProtocol.ERROR}You are not registered"
            self.client_socket.send(error_message.encode())
            return
        chat_message = AkinProtocol.strip_delimiter(client_msg)
        card_name = str(self.card.name)
        apartment_no = str(self.card.apartment_no)

        chat_message = f"[{Utility.get_simple_time()}] [Apt No:{apartment_no}] {card_name}: {chat_message}"
        chat_message = AkinProtocol.construct_chat_message(chat_message)

        if self.subscribed_to_message_channel:
            self.message_queue.put(chat_message)
            self.client_socket.send(AkinProtocol.OK.encode())
        else:
            error_message = f"{AkinProtocol.ERROR}You are not subscribed to the message channel"
            self.client_socket.send(error_message.encode())

    def __handle_get_weather(self, client_msg: str) -> None:
        """Handles the get weather command"""
        weather_message = AkinProtocol.construct_weather_response(self.weather)
        self.client_socket.send(weather_message.encode())

    def __handle_get_currency(self, client_msg: str) -> None:
        """Handles the get currency command"""
        currency_message = AkinProtocol.construct_currency_response(self.currency)
        self.client_socket.send(currency_message.encode())


class ServerManagementThread(threading.Thread):
    """A thread to manage the server. This thread will remove closed connections and update weather and currency for clients"""

    def __init__(self, server: Server):
        super().__init__(daemon=True)
        self.server = server
        self.UPDATE_RATE = 180  # Updates the weather and currency data every X seconds
        self.running_flag = True
        self.logger = self.server.logger

    def run(self):
        # Start a thread to remove closed connections
        remove_closed_connections_thread = threading.Thread(target=self.__remove_stopped_connections, daemon=True)
        update_weather_thread = threading.Thread(target=self.__update_weather_for_clients, daemon=True)
        update_currency_thread = threading.Thread(target=self.__update_currency_for_clients, daemon=True)
        remove_closed_connections_thread.start()
        update_weather_thread.start()
        update_currency_thread.start()

        while self.running_flag:
            if __name__ == '__main__':
                self.__console_command_listener()
            time.sleep(1)

    def command_change_update_rate(self, new_rate: int) -> None:
        self.UPDATE_RATE = new_rate
        self.logger.put(f"Update rate changed to {new_rate} seconds")

    def command_stop_server(self):
        """Stops the server"""
        self.running_flag = False
        self.server.stop_server()
        self.logger.put("Server stopped")

    def command_open_connections(self):
        """Returns a list of the names of the open connections"""
        connection_list = [thread.client_address for thread in self.server.open_connection_threads]
        return connection_list

    def __console_command_listener(self) -> None:
        """Listens for commands from the console
        For debugging purposes only"""
        command = input("-->")
        if command in ["stop_server", "exit"]:
            self.server.server_socket.close()
            for thread in self.server.open_connection_threads:
                thread.close_connection()
            self.running_flag = False
        elif command == "open_connections_count":
            print("Open connections: ", len(self.server.open_connection_threads))
        elif command == "list_names_of_open_connections":
            for thread in self.server.open_connection_threads:
                print(thread.client_address)
        elif command == "help":
            print("Available commands: stop_server, exit, open_connections, help, list_names_of_open_connections")

    def __remove_stopped_connections(self):
        """Removes stopped connections from the list of open connections"""
        while self.running_flag:
            time.sleep(0.5)
            for thread in self.server.open_connection_threads:
                if not thread.is_connection_open() or not thread.is_alive():
                    self.server.open_connection_threads.remove(thread)
                    self.logger.put(f"Following client just disconnected: {thread.client_address}")

    def __update_weather_for_clients(self):
        """Updates the weather for all client threads"""
        while self.running_flag:
            self.server.update_weather()
            for thread in self.server.open_connection_threads:
                thread.update_weather(self.server.get_weather())
            time.sleep(self.UPDATE_RATE)
            self.logger.put("UPDATED WEATHER | Weather data has been updated from weather.com")

    def __update_currency_for_clients(self):
        """Updates the currency for all client threads"""
        while self.running_flag:
            self.server.update_currency()
            for thread in self.server.open_connection_threads:
                thread.update_currency(self.server.get_currency())
            time.sleep(self.UPDATE_RATE)
            self.logger.put("UPDATED CURRENCY | Currency data has been updated from doviz.com")


def main():
    server = Server('0.0.0.0', 9000)
    server.start()


if __name__ == '__main__':
    main()
