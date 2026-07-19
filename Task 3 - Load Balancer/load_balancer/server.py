"""
Represents a physical server in the consistent hash ring.
Each physical server is represented by multiple virtual servers.
"""


class Server:
    """
    Represents one physical server.
    """

    def __init__(self, server_id):
        """
        Initialize a server.

        Parameters
       
        server_id : int
            Unique ID of the physical server.
        """
        self.server_id = server_id

    def __str__(self):
        return f"Server {self.server_id}"

    def __repr__(self):
        return self.__str__()
