class APIError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)  # Call the base Exception constructor
        self.message = message
        self.status_code = status_code
