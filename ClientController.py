import multiprocessing
import threading

import AkinProtocol
import custom_exceptions as ce
from Client import Client
from ClientCard import ClientCard


class ClientController:
    """This class is responsible for communicating the Client code with the GUI of the client. Following the MVC pattern."""

    def __init__(self, host: str, port: int):
        self.client = None
        self.host = host
        self.port = port
        self.card = None
        self.client_running = False
        self.message_queue = None

    def start_client(self, host, port):
        """Starts the client. Returns True if the client is started successfully, otherwise raises an exception.
        Exceptions:
            ClientAlreadyRunningError: If the client is already running.
            InvalidPortError: If the port is invalid.
        """
        self.host = host
        self.port = port
        if self.client_running:
            raise ce.ClientAlreadyRunningError("Client is already running.")

        self.client = Client(self.host, self.port)
        self.message_queue = self.client.get_message_queue()
        client_thread = threading.Thread(target=self.client.start)
        client_thread.start()
        try:
            msg = self.message_queue.get(block=True, timeout=5)
        except Exception as e:
            msg = ""
        if msg != AkinProtocol.WELCOME_TO_THE_SERVER:
            raise ce.NoServersFoundOnThisHostAndPortError("No servers were found on this host and port!")
        self.client_running = True
        return True

    def register_client(self, card: ClientCard) -> bool:
        """Registers the client. Returns True if the client is registered successfully, otherwise raises an exception.
        Exceptions:
            ClientNotRunningError: If the client is not running.
            ClientCouldNotRegisterError: If the client could not register.
        """
        if not self.client_running:
            raise ce.ClientNotRunningError("Client is not running.")
        self.client.register_client(card)
        return True

    def get_message_queue(self) -> multiprocessing.Queue:
        """Returns the message queue."""
        if not self.client_running:
            raise ce.ClientNotRunningError("Client is not running.")
        if self.message_queue is None:
            raise ce.MessageQueueNotInitializedError("Message queue not initialized.")
        return self.message_queue

    def stop_client(self) -> bool:
        """Stops the client. Returns True if the client is stopped successfully, otherwise raises an exception.
        Exceptions:
            ClientNotRunningError: If the client is not running.
            ClientCouldNotBeClosedError: If the client could not be closed.
        """
        if not self.client_running:
            raise ce.ClientNotRunningError("Client is not running.")
        if client_closed := self.client.close_connection():
            self.client_running = False
            return True
        else:
            raise ce.ClientCouldNotBeClosedError("Client could not be closed.")

    def send_message(self, message: str) -> bool:
        """Sends a message to the server. Returns True if the message was sent successfully, otherwise raises an exception.
        Exceptions:
            ClientNotRunningError: If the client is not running.
        """
        if not self.client_running:
            raise ce.ClientNotRunningError("Client is not running.")
        self.client.send_chat_message(message)
        return True

    def subscribe_to_message_channel(self) -> bool:
        """Subscribes to the message channel. Returns True if the client is subscribed successfully, otherwise raises an exception.
        Exceptions:
            ClientNotRunningError: If the client is not running.
            ClientCouldNotSubscribeError: If the client could not subscribe.
        """
        if not self.client_running:
            raise ce.ClientNotRunningError("Client is not running.")
        self.client.subscribe_to_message_channel()
        return True

    def unsubscribe_from_message_channel(self) -> bool:
        """Unsubscribes from the message channel. Returns True if the client is unsubscribed successfully, otherwise raises an exception.
        Exceptions:
            ClientNotRunningError: If the client is not running.
            ClientCouldNotUnsubscribeError: If the client could not unsubscribe.
        """
        if not self.client_running:
            raise ce.ClientNotRunningError("Client is not running.")
        self.client.unsubscribe_from_message_channel()
        return True

    def get_weather(self):
        """Returns the weather."""
        if not self.client_running:
            raise ce.ClientNotRunningError("Client is not running.")
        return self.client.weather_data

    def get_currency(self):
        """Returns the currency."""
        if not self.client_running:
            raise ce.ClientNotRunningError("Client is not running.")
        return self.client.currency_data
