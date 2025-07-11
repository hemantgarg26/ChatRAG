from enum import Enum

class ErrorAndSuccessCodes(Enum):
    # 0xx: Success
    SUCCESS = 1

    # General Errors
    INVALID_INPUT = 2
    GLOBAL_RATE_LIMIT_EXHAUSTED = 3
    USER_RATE_LIMIT_EXHAUSTED = 4

    # Processing Status
    MESSAGE_UNDER_PROCESSING = 5
    MESSAGE_PROCESSING_SUCCESS = 6

    #Error
    PROCESSING_ERROR = 7