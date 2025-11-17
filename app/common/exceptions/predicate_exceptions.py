class RateLimitExceededException(Exception):
    __client_id: str

    @property
    def client_id(self):
        return self.__client_id

    def __init__(self,  client_id: str, message="Rate limit exceeded."):
        self.__client_id = client_id
        self.message = message
        super().__init__(self.message)
