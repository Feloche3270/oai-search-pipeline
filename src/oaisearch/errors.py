class OAIError(Exception):
    """Exception raised for OAI Error"""

    def __init__(self, code: str, message: str) -> None:
        self.message = message
        self.code = code
        super().__init__(f"{self.code}: {self.message}")


class HarvestError(Exception):
    """Exception raised for an invalid XML response"""


class EsConnectionError(Exception):
    """Exception raised when Elasticsearch isn't running"""
