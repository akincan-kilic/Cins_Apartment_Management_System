import threading
import socket
import time

class ClientHandlerThread(threading.Thread):
    def __init__(self, client_socket:socket.socket, client_address):
        super().__init__()
        self.special_delimiter = "|<<!?!>>|"
        self.client_socket = client_socket
        self.client_address = client_address
        self.connection_open = False

    def run(self) -> None:
        """Handle a client connection"""
        self.connection_open = True
        self.client_socket.send(f"Welcome to the server! {self.client_socket.getpeername()}".encode())
        while True:
            data = self.client_socket.recv(1024).decode()
            if not data:
                self.connection_open = False
                break
            if data == f"get_weather{self.special_delimiter}":
                # print("Sending weather data to client...")
                self.client_socket.send("It's sunny today!".encode())
            elif data == f"get_currency{self.special_delimiter}":
                # print("Sending currency data to client...")
                self.client_socket.send("1$ = 18.67₺".encode())
            else: # Chat message
                # print("Received message from client:", data)
                self.client_socket.send(f"ACK: {data}".encode())
        self.connection_open = False
        self.client_socket.close()

    def is_connection_open(self):
        return self.connection_open

class ThreadedServer(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.open_connection_threads = []
        self.server_management_thread = ServerManagementThread(self)


    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        print(f"Server started on {self.host}:{self.port}")
        # Start a thread to check for closed connections
        self.server_management_thread.start()
        # Start accepting connections from clients.
        # A new thread will be created for each client.
        while True:
            # print("Waiting for connection...")
            (client_socket, address) = self.server_socket.accept()
            # print("Accepted connection from: ", address)
            client_thread = ClientHandlerThread(client_socket, address)
            client_thread.start()
            self.open_connection_threads.append(client_thread)


class ServerManagementThread(threading.Thread):
    def __init__(self, server:ThreadedServer):
        super().__init__(daemon=True)
        self.server = server

    def run(self):
        # Start a thread to remove closed connections
        remove_closed_connections_thread = threading.Thread(target=self.remove_stopped_connections, daemon=True)
        remove_closed_connections_thread.start()
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


def main():
    server = ThreadedServer('localhost', 9999)
    server.start()

if __name__ == '__main__':
    main()
