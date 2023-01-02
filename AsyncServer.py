import asyncio

class TCPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = None

    async def start(self):
        print("Starting server...")
        self.server = await asyncio.start_server(self.accept_connection, self.host, self.port)
        await self.server.serve_forever()

    async def accept_connection(self, reader, writer):
        print("Accepted connection from:", writer.get_extra_info("peername"))
        while True:
            data = await reader.read(1024)
            if not data:
                break
            await self.receive_data(data, writer)
        writer.close()

    async def receive_data(self, data, writer):
        print("Received data:", data.decode())
        writer.write(data)


async def main():
    server = TCPServer("localhost", 5000)
    await server.start()

if __name__ == '__main__':
    asyncio.run(main())
