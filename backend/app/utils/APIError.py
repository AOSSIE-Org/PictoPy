class APIError(Exception):
    """
    Custom exception class to represent API errors with an associated
    HTTP status code and an error message.
    """
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)  # Call the base Exception constructor
        self.message = message
        self.status_code = status_code
