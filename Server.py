from __future__ import annotations

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
from Weather import WeatherDataFetcher


class Server(threading.Thread):
    """A threaded server that handles multiple clients"""

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.running_flag = True

        ### Queues For Multi-Process Communication ###
        self.message_queue = multiprocessing.Queue()
        self.logging_queue = multiprocessing.Queue()

        ### Server Helper Threads ###
        self.open_connection_threads: list[ClientThread] = []
        self.group_chat_updater_thread = threading.Thread(target=self.__update_group_chat, daemon=False)
        self.currency_updater_thread = threading.Thread(target=self.__update_currency_for_clients, daemon=True)
        self.weather_updater_thread = threading.Thread(target=self.__update_weather_for_clients, daemon=True)
        self.open_connection_checker_thread = threading.Thread(target=self.__remove_stopped_connections, daemon=True)

        ### Weather and currency data ###
        self.weather_data_fetcher = WeatherDataFetcher()
        self.currency_data_fetcher = CurrencyDataFetcher()
        self.weather = AkinProtocol.DEFAULT_WEATHER_DICT
        self.currency = AkinProtocol.DEFAULT_CURRENCY_DICT
        self.UPDATE_RATE = AkinProtocol.DEFAULT_UPDATE_RATE  # Updates the weather and currency data every X seconds

    def run(self):
        self.__bind_and_listen()
        self.__start_helper_threads()
        while self.running_flag:
            try:
                self.__accept_client_to_a_new_thread()
            except ConnectionAbortedError:
                break  # Server is closed
        sys.exit(0)

    ### -------------- ###
    ### Public Methods ###
    ### -------------- ###

    def change_update_rate(self, new_rate: int) -> None:
        self.UPDATE_RATE = new_rate
        self.logging_queue.put(f"Update rate changed to {new_rate} seconds, it will be applied after the next update.")

    def get_open_connections(self) -> list[str]:
        """Returns a list of the names of the open connections"""
        connection_list = []
        for client_thread in self.open_connection_threads:
            out_str = ""
            if client_thread.card is not None:
                out_str += f"{client_thread.card.name} - {client_thread.card.apartment_no} -> [{client_thread.client_address}]"
            else:
                out_str += f"[{client_thread.client_address}]"
            connection_list.append(out_str)
        return connection_list

    def stop_server(self):
        """Stops the server"""
        self.running_flag = False
        self.server_socket.close()
        for client in self.open_connection_threads:
            client.close_connection()
        self.logging_queue.put("Server stopped")
        sys.exit(0)

    ### -------------- ###
    ### Socket Methods ###
    ### -------------- ###
    def __bind_and_listen(self):
        """Binds the server to the given host and port and starts listening for connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.running_flag = True
            self.logging_queue.put(f"Server successfully started on [{self.host}:{self.port}]")
            self.logging_queue.put("Waiting for a connection...")
        except socket.error as e:
            raise ce.InvalidPortError(f"Error binding to port {self.port}: {e}") from e

    def __accept_client_to_a_new_thread(self):
        """Accepts a client connection and starts a new thread to handle it"""
        (client_socket, address) = self.server_socket.accept()
        self.logging_queue.put(f"Accepted connection from: {address}, started a new thread to handle this client.")
        client_thread = ClientThread(client_socket, address, self.message_queue, self.weather, self.currency,
                                     self.logging_queue)
        client_thread.start()
        self.open_connection_threads.append(client_thread)

    ### -------------- ###
    ### Helper Methods ###
    ### -------------- ###

    def __update_weather(self) -> None:
        """Updates the weather data from the weather data fetcher and returns the weather data"""
        weather = self.weather_data_fetcher.fetch_weather_data(city='Manisa')
        self.weather = weather

    def __update_currency(self) -> None:
        """Updates the currency data from the currency data fetcher and returns the currency data"""
        currency = self.currency_data_fetcher.fetch_exchange_rates()
        self.currency = currency

    ### ------- ###
    ### Threads ###
    ### ------- ###

    def __start_helper_threads(self):
        self.group_chat_updater_thread.start()
        self.currency_updater_thread.start()
        self.weather_updater_thread.start()
        self.open_connection_checker_thread.start()

    def __update_group_chat(self):
        while self.running_flag:
            if not self.message_queue.empty():
                msg = self.message_queue.get()
                for client in self.open_connection_threads:
                    if client.subscribed_to_message_channel:
                        client.client_socket.send(msg.encode())
            time.sleep(0.1)

    def __remove_stopped_connections(self):
        """Removes stopped connections from the list of open connections"""
        while self.running_flag:
            time.sleep(0.5)
            for thread in self.open_connection_threads:
                if not thread.is_connection_open() or not thread.is_alive():
                    self.open_connection_threads.remove(thread)
                    if thread.card is not None:
                        self.logging_queue.put(f"{thread.card.name} - {thread.card.apartment_no} has left the apartment!")
                    else:
                        self.logging_queue.put(f"Following client just left the apartment: {thread.client_address}")

    def __update_weather_for_clients(self):
        """Updates the weather for all client threads"""
        while self.running_flag:
            self.__update_weather()
            for thread in self.open_connection_threads:
                thread.update_weather(self.weather)
            time.sleep(self.UPDATE_RATE)
            self.logging_queue.put("UPDATED WEATHER | Weather data has been updated from weather.com")

    def __update_currency_for_clients(self):
        """Updates the currency for all client threads"""
        while self.running_flag:
            self.__update_currency()
            for thread in self.open_connection_threads:
                thread.update_currency(self.currency)
            time.sleep(self.UPDATE_RATE)
            self.logging_queue.put("UPDATED CURRENCY | Currency data has been updated from doviz.com")


class ClientThread(threading.Thread):
    """A thread that handles a single client connection"""

    def __init__(self, client_socket: socket.socket, client_address, msg_queue: multiprocessing.Queue, weather: dict,
                 currency: dict, logging_queue: multiprocessing.Queue):
        super().__init__()
        self.client_socket = client_socket
        self.client_address = client_address
        self.message_queue = msg_queue
        self.logging_queue = logging_queue
        self.weather = weather
        self.currency = currency
        self.card: ClientCard = None  # type: ignore
        self.subscribed_to_message_channel = False
        self.connection_open_flag = False

    def run(self) -> None:
        """Handle a client connection"""
        self.connection_open_flag = True
        self.client_socket.send(AkinProtocol.WELCOME_TO_THE_SERVER.encode())
        while self.connection_open_flag:
            try:
                client_msg = self.client_socket.recv(1024).decode()
            except ConnectionResetError:
                self.connection_open_flag = False
                break
            self.__handle_client_message(client_msg=client_msg)
        sys.exit(0)

    ### -------------- ###
    ### Public Methods ###
    ### -------------- ###

    def is_connection_open(self) -> bool:
        return self.connection_open_flag

    def close_connection(self) -> None:
        self.connection_open_flag = False
        self.client_socket.close()

    ### -------------- ###
    ### Helper Methods ###
    ### -------------- ###

    def update_weather(self, weather: dict) -> None:
        """Updates the weather data that the client will receive when requested"""
        self.weather = weather

    def update_currency(self, currency: dict) -> None:
        """Updates the currency data that the client will receive when requested"""
        self.currency = currency

    ### -------------- ###
    ### Socket Methods ###
    ### -------------- ###

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
        self.logging_queue.put(f"{self.card.name} [{self.card.apartment_no}] just scanned their card and entered the apartment!")

    def __handle_subscribe_request(self, client_msg: str) -> None:
        """Handles the subscribe request command, this will add the client to the message channel"""
        self.subscribed_to_message_channel = True
        self.client_socket.send(AkinProtocol.OK.encode())
        self.logging_queue.put(f"{self.card.name} [{self.card.apartment_no}] subscribed to the message channel.")

    def __handle_unsubscribe_request(self, client_msg: str) -> None:
        """Handles the unsubscribe request command, this will remove the client from the message channel"""
        self.subscribed_to_message_channel = False
        self.client_socket.send(AkinProtocol.OK.encode())
        self.logging_queue.put(f"{self.card.name} [{self.card.apartment_no}] unsubscribed from the message channel.")

    def __handle_chat_message(self, client_msg: str) -> None:
        if self.card is None:
            error_message = f"{AkinProtocol.ERROR}You are not registered"
            self.client_socket.send(error_message.encode())
            return
        chat_message = AkinProtocol.strip_delimiter(client_msg)
        card_name = str(self.card.name)
        apartment_no = str(self.card.apartment_no)

        chat_message = f"[{Utility.get_simple_time()}] [No:{apartment_no}] {card_name}: {chat_message}"
        chat_message = AkinProtocol.construct_chat_message(chat_message)

        if self.subscribed_to_message_channel:
            self.message_queue.put(chat_message)
            self.client_socket.send(AkinProtocol.OK.encode())
            self.logging_queue.put(f"{self.card.name} [{self.card.apartment_no}] sent a message to the group chat.")
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


def main():
    server = Server('0.0.0.0', 9000)
    server.start()


if __name__ == '__main__':
    main()
