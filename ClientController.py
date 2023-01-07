import custom_exceptions as ce
from Client import Client
from ClientCard import ClientCard
import multiprocessing
import threading

class ClientController:
    """This class is responsible for communucating the Client code with the GUI of the client. Following the MVC pattern."""
    def __init__(self, host:str, port:int, card:ClientCard):
        self.host = host
        self.port = port
        self.card = card
        self.client_running = False
        self.message_queue = None

    def start_client(self, host, port) -> bool:
        """Starts the client. Returns True if the client is started successfully, otherwise raises an exception.
        Exceptions:
            ClientAlreadyRunningError: If the client is already running.
            InvalidPortError: If the port is invalid.
        """
        self.host = host
        self.port = port
        if self.client_running:
            raise ce.ClientAlreadyRunningError("Client is already running.")
        try:
            self.client = Client(self.host, self.port)
            self.message_queue = self.client.get_message_queue()
            threading.Thread(target=self.client.start).start()
            self.client_running = True
            return True
        except ce.InvalidPortError as e:
            raise e

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
        if (client_closed := self.client.close_connection()):
            self.client_running = False
            return True
        else:
            raise ce.ClientCouldNotBeClosedError("Client could not be closed.")

    def send_message(self, message:str) -> bool:
        """Sends a message to the server. Returns True if the message was sent successfully, otherwise raises an exception.
        Exceptions:
            ClientNotRunningError: If the client is not running.
        """
        if not self.client_running:
            raise ce.ClientNotRunningError("Client is not running.")
        self.client.send_chat_message(message)

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