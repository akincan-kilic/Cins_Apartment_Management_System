import multiprocessing
import threading
import socket
import time
from weather import WeatherDataFetcher
from currency import CurrencyDataFetcher
import AkinProtocol

class ClientHandlerThread(threading.Thread):
    def __init__(self, client_socket:socket.socket, client_address, msg_queue: multiprocessing.Queue, weather:str, currency:str):
        super().__init__()
        self.special_delimiter = "|<<!?!>>|"
        self.client_socket = client_socket
        self.client_address = client_address
        self.connection_open = False
        self.weather = weather
        self.currency = currency
        self.message_queue = msg_queue
        self.subscribed_to_message_channel = False

    def update_weather(self, weather:str):
        self.weather = weather

    def update_currency(self, currency:str):
        self.currency = currency

    def run(self) -> None:
        """Handle a client connection"""
        self.connection_open = True
        self.client_socket.send(f"Welcome to the server! {self.client_socket.getpeername()}".encode())
        while True:
            data = self.client_socket.recv(1024).decode()
            if not data:
                self.connection_open = False
                break
            if data == f"WTH{self.special_delimiter}":
                self.client_socket.send(f"WTH{self.weather}".encode())
            elif data == f"CUR{self.special_delimiter}":
                self.client_socket.send(f"CUR{self.currency}".encode())
            elif data == f"SUB{self.special_delimiter}":
                self.subscribed_to_message_channel = True
                self.client_socket.send(AkinProtocol.OK.encode())
            elif data == f"USB{self.special_delimiter}":
                self.subscribed_to_message_channel = False
                self.client_socket.send(AkinProtocol.OK.encode())
            elif data.startswith("MSG"):
                if self.subscribed_to_message_channel:
                    self.message_queue.put(data)
                    self.client_socket.send(AkinProtocol.OK.encode())

        self.connection_open = False
        self.client_socket.close()

    def is_connection_open(self):
        return self.connection_open

class ThreadedServer(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.msg_queue = multiprocessing.Queue()
        self.open_connection_threads = []
        self.server_management_thread = ServerManagementThread(self)
        self.weather_data_fetcher = WeatherDataFetcher()
        self.currency_data_fetcher = CurrencyDataFetcher()
        self.group_chat_updater_thread = threading.Thread(target=self.__update_group_chat)
        self.group_chat_updater_thread.start()
        self.weather = ""
        self.currency = ""

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        print(f"Server started on {self.host}:{self.port}")
        # Start a thread to check for closed connections
        self.server_management_thread.start()
        # Start accepting connections from clients. A new thread will be created for each client.
        while True:
            # print("Waiting for connection...")
            (client_socket, address) = self.server_socket.accept()
            # print("Accepted connection from: ", address)
            client_thread = ClientHandlerThread(client_socket, address, self.msg_queue, self.weather, self.currency)
            client_thread.start()
            self.open_connection_threads.append(client_thread)

    def __update_group_chat(self):
        while True:
            if not self.msg_queue.empty():
                msg = self.msg_queue.get()
                for client in self.open_connection_threads:
                    if client.subscribed_to_message_channel:
                        client.client_socket.send(msg.encode())
            time.sleep(0.1)

    def update_weather(self):
        weather = self.weather_data_fetcher.get_manisa_weather_data()
        self.weather = weather
        return weather

    def update_currency(self):
        currency = self.currency_data_fetcher.fetch_exchange_rates()
        self.currency = currency
        return currency

    def get_weather(self):
        return self.weather

    def get_currency(self):
        return self.currency

class ServerManagementThread(threading.Thread):
    def __init__(self, server:ThreadedServer):
        super().__init__(daemon=True)
        self.server = server
        self.UPDATE_RATE = 1

    def run(self):
        # Start a thread to remove closed connections
        remove_closed_connections_thread = threading.Thread(target=self.remove_stopped_connections, daemon=True)
        update_weather_thread = threading.Thread(target=self.update_weather_for_clients, daemon=True)
        update_currency_thread = threading.Thread(target=self.update_currency_for_clients, daemon=True)
        remove_closed_connections_thread.start()
        update_weather_thread.start()
        update_currency_thread.start()

        while True:
            command = input("-->")
            if command == "stop_server":
                self.server.server_socket.close()
                break
            elif command == "open_connections":
                print("Open connections: ", len(self.server.open_connection_threads))
            elif command == "list_names_of_open_connections":
                for thread in self.server.open_connection_threads:
                    print(thread.client_address)
            elif command == "help":
                print("Available commands: stop_server, open_connections, help, list_names_of_open_connections")

    def remove_stopped_connections(self):
        while True:
            time.sleep(0.5)
            for thread in self.server.open_connection_threads:
                if not thread.is_connection_open() or not thread.is_alive():
                    self.server.open_connection_threads.remove(thread)
                    # print("Removed closed connection: ", thread.client_address)

    def update_weather_for_clients(self):
        while True:
            self.server.update_weather()
            for thread in self.server.open_connection_threads:
                thread.update_weather(self.server.get_weather())
            time.sleep(self.UPDATE_RATE)

    def update_currency_for_clients(self):
        while True:
            self.server.update_currency()
            for thread in self.server.open_connection_threads:
                thread.update_currency(self.server.get_currency())
            time.sleep(self.UPDATE_RATE)

def main():
    server = ThreadedServer('localhost', 9999)
    server.start()

if __name__ == '__main__':
    main()
