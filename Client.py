import multiprocessing
import socket
import threading
import time

import AkinProtocol


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.message_queue = multiprocessing.Queue()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message = ""
        self.subscribed_to_message_channel = False
        self.client_manager_thread = ClientListenerThread(self, self.message_queue)
        self.weather_data = {'temperature': 0, 'wind_speed': 0, 'wind_direction': 0}
        self.currency_data = {'usd': 0, 'eur': 0}

    def start(self):
        self.socket.connect((self.host, self.port))
        print("Connected to server")
        welcome_message = self.socket.recv(1024).decode()  # Receive the welcome message from the server
        print(welcome_message)
        self.client_manager_thread.start()

        while True:
            self.send_weather_request()
            time.sleep(5)
            self.send_currency_request()
            time.sleep(5)

    def get_message_queue(self):
        return self.message_queue

    def subscribe_to_message_channel(self):
        self.send_message(AkinProtocol.SUBSCRIBE_REQUEST)

    def unsubscribe_from_message_channel(self):
        self.send_message(AkinProtocol.UNSUBSCRIBE_REQUEST)

    def send_weather_request(self):
        self.send_message(AkinProtocol.WEATHER_GET)

    def send_currency_request(self):
        self.send_message(AkinProtocol.CURRENCY_GET)

    def send_message(self, message):
        self.socket.send(message.encode())

    def receive_message(self) -> str:
        return self.socket.recv(1024).decode()

    def send_chat_message(self, message):
        message_to_send = AkinProtocol.construct_chat_message(message)
        self.socket.send(message_to_send.encode())
        return True

    def register_client(self, card):
        message_to_send = AkinProtocol.register_client_to_server(card)
        self.socket.send(message_to_send.encode())

    def close_connection(self):
        self.client_manager_thread.stop()
        self.socket.close()


class ClientListenerThread(threading.Thread):
    def __init__(self, client, message_queue):
        super().__init__()
        self.client = client
        self.message_queue = message_queue
        self.running_flag = True

    def run(self):
        while self.running_flag:
            msg: str = self.client.receive_message()
            if not msg:
                print("Connection to server lost")
                break

            if msg.startswith(AkinProtocol.WEATHER_GET):
                data = AkinProtocol.strip_delimiter(msg)
                # print("Weather data received from server:", data)
                self.client.weather_data = eval(data)

            elif msg.startswith(AkinProtocol.CURRENCY_GET):
                data = AkinProtocol.strip_delimiter(msg)
                # print("Currency data received from server:", data)
                self.client.currency_data = eval(data)

            elif msg.startswith(AkinProtocol.CHAT_MESSAGE):
                data = AkinProtocol.strip_delimiter(msg)
                self.message_queue.put(data)
                print("Put message in queue:", data)

            elif msg.startswith(AkinProtocol.OK):
                print("OK message received from server")

            elif msg.startswith(AkinProtocol.ERROR):
                data = AkinProtocol.strip_delimiter(msg)
                print(f"ERROR message received from server | Reason: {data}")

            else:
                print("Unknown message received from server:", msg)

    def stop(self):
        self.running_flag = False


def main():
    Client("0.0.0.0", 8080).start()


if __name__ == '__main__':
    main()
