import custom_exceptions as ce
from Server import Server


class ServerController:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server = Server(self.host, self.port)
        self.server_running = False
        self.logger = self.server.logging_queue

    def start_server(self) -> bool:
        """Starts the server. Returns True if the server is started successfully, otherwise raises an exception.
        Exceptions:
            ServerAlreadyRunningError: If the server is already running.
            InvalidPortError: If the port is invalid.
        """
        if self.server_running:
            raise ce.ServerAlreadyRunningError("Server is already running.")
        try:
            self.server.start()
            self.server_running = True
            return True
        except ce.InvalidPortError as e:
            raise e

    def stop_server(self) -> bool:
        """Stops the server. Returns True if the server is stopped successfully, otherwise raises an exception.
        Exceptions:
            ServerNotRunningError: If the server is not running.
            ServerCouldNotBeClosedError: If the server could not be closed.
        """
        if not self.server_running:
            raise ce.ServerNotRunningError("Server is not running.")
        if self.server.stop_server():
            self.server_running = False
            return True
        else:
            raise ce.ServerCouldNotBeClosedError("Server could not be closed.")

    def get_open_connections(self) -> list:
        """Returns a list of all open connections."""
        return self.server.get_open_connections()

    def change_update_rate(self, update_rate: str) -> None:
        """Changes the update rate of the server."""
        # Only allow ints as update rate.
        try:
            update_rate = int(update_rate)
        except ValueError as e:
            raise ValueError("Update rate should be an integer.") from e
        if not isinstance(update_rate, int):
            raise TypeError("Update rate must be an integer.")
        if update_rate < 10:
            raise ValueError("Update rate cannot be less than 10 seconds.")
        self.server.change_update_rate(update_rate)
