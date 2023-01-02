import threading
import socket
import time
import AkinProtocol

class ThreadedClient(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.special_delimiter = "|<<!?!>>|"
        self.message = ""
        self.subscribed_to_message_channel = False
        self.__client_manager_thread = ClientManagmentThread(self)

    def run(self):
        self.socket.connect((self.host, self.port))
        print("Connected to server")
        welcome_message = self.socket.recv(1024).decode() # Receive the welcome message from the server
        print(welcome_message)

        self.__client_manager_thread.start()
        self.subscribe_to_message_channel()

        while True:
            if self.send_message_flag:
                self.__send_chat_message()
            if self.get_weather_flag:
                self.__send_weather_request()
            if self.get_currency_flag:
                self.__send_currency_request()
            time.sleep(0.1)


    def subscribe_to_message_channel(self):
        self.__send_message(AkinProtocol.SUBSCRIBE_TO_MESSAGE_CHANNEL)
        if self.receive_message() == AkinProtocol.OK:
            self.subscribed_to_message_channel = True

    def unsubscribe_from_message_channel(self):
        self.__send_message(f"USB{self.special_delimiter}")
        if self.receive_message() == AkinProtocol.OK:
            self.subscribed_to_message_channel = False



    def __send_message(self, message):
        self.socket.send(message.encode())

    def receive_message(self):
        data = self.socket.recv(1024).decode()
        print("Received data from server:", data)
        return data

    def __send_chat_message(self):
        self.__send_message(self.message)

    def __send_weather_request(self):
        self.__send_message(AkinProtocol.WEATHER)

    def __send_currency_request(self):
        self.__send_message(AkinProtocol.CURRENCY)

    def send_message_to_chat(self, message):
        # self.message = message
        self.message = input("Enter message to send to server: ")



class ClientManagmentThread(threading.Thread):
    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        while True:
            msg = self.client.receive_message()
            if msg.startswith("WTH"):
                print("Weather data received from server:", msg[3:])
            elif msg.startswith("CUR"):
                print("Currency data received from server:", msg[3:])
            elif msg.startswith("MSG"):
                print("Message received from server:", msg[3:])
            else:
                print("Unknown message received from server:", msg)

def main():
    client_thread = ThreadedClient("localhost", 9999)
    client_thread.start()
    while True:
        # client_thread.get_weather_from_server()
        # time.sleep(5)
        # client_thread.get_currency_from_server()
        # time.sleep(5)
        client_thread.send_message_to_chat("Sending a hello message in the loop")
        # time.sleep(5)

if __name__ == '__main__':
    main()