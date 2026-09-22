from enum import Enum


class Role(str, Enum):
    USER = "user"
    RICK = "rick"
    SYSTEM = "system"


class User(str, Enum):
    RICK = "rick"
