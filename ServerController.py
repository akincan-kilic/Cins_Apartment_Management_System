import custom_exceptions as ce
from Server import Server


class ServerController:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server = Server(self.host, self.port)
        self.server_running = False
        self.logger = self.server.logger

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
        if server_closed := self.server.server_management_thread.command_stop_server():
            self.server_running = False
            return True
        else:
            raise ce.ServerCouldNotBeClosedError("Server could not be closed.")

    def get_open_connections(self) -> list:
        """Returns a list of all open connections."""
        return self.server.server_management_thread.command_open_connections()
