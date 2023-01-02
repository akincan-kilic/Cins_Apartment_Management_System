import asyncio

class TCPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        print("Connecting to server...")
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def send_data(self, data):
        self.writer.write(data)
        await self.writer.drain()

    async def receive_data(self):
        data = await self.reader.read(1024)
        return data.decode()

    async def close(self):
        self.writer.close()


async def main():
    client = TCPClient("localhost", 9999)
    await client.connect()

    while True:
        msg = input("Enter message to send to server: ")
        if msg == "exit":
            break
        await client.send_data(msg.encode())
        response = await client.receive_data()
        print("Received from server:", response)
    await client.close()

if __name__ == '__main__':
    asyncio.run(main())
