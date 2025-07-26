class APIError(Exception):
    """
    Custom exception class for API errors.
    Stores an error message and an HTTP status code (default is 400).
    """
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)  # Call the base Exception constructor
        self.message = message
        self.status_code = status_code
