import jdp

class Client:
    def __init__(self,
                 server_host: str = "127.0.0.1",
                 server_port: int = 11000):
        self.server = jdp.Client((server_host, server_port))

    def send(self, data: dict):
        self.server.send(data)
