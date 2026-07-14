"""
Represents a client request.
Each request has a unique request ID.
"""


class Request:
    """
    Represents one client request.
    """

    def __init__(self, request_id):
        """
        Initialize a request.

        Parameters
        ----------
        request_id : int
            Unique request ID.
        """
        self.request_id = request_id

    def __str__(self):
        return f"Request({self.request_id})"

    def __repr__(self):
        return self.__str__()