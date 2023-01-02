import threading
import socket
import time

class ThreadedClient(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.special_delimiter = "|<<!?!>>|"
        self.message = ""
        self.send_message_flag = False
        self.get_weather_flag = False
        self.get_currency_flag = False

    def run(self):
        self.socket.connect((self.host, self.port))
        print("Connected to server")
        # Receive the welcome message from the server
        welcome_message = self.socket.recv(1024).decode()
        print(welcome_message)
        while True:
            if self.send_message_flag:
                self.__handle_message()
            if self.get_weather_flag:
                self.__handle_weather()
            if self.get_currency_flag:
                self.__handle_currency()

    def send_message_to_chat(self, message):
        self.message = message
        self.send_message_flag = True

    def __send_message(self, message):
        self.socket.send(message.encode())

    def __receive_message(self):
        data = self.socket.recv(1024).decode()
        print("Received data from server:", data)
        return data

    def __handle_message(self):
        self.__send_message(self.message)
        data = self.__receive_message()
        self.send_message_flag = False

    def get_weather_from_server(self):
        self.get_weather_flag = True

    def __handle_weather(self):
        self.__send_message(f"get_weather{self.special_delimiter}")
        data = self.__receive_message()
        self.get_weather_flag = False

    def get_currency_from_server(self):
        self.get_currency_flag = True

    def __handle_currency(self):
        self.__send_message(f"get_currency{self.special_delimiter}")
        data = self.__receive_message()
        self.get_currency_flag = False


def main():
    client_thread = ThreadedClient("localhost", 9999)
    client_thread.start()
    while True:
        client_thread.get_weather_from_server()
        time.sleep(5)
        client_thread.get_currency_from_server()
        time.sleep(5)
        client_thread.send_message_to_chat("Sending a hello message in the loop")
        time.sleep(5)

if __name__ == '__main__':
    main()