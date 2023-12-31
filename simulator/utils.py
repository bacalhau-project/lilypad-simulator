from dataclasses import dataclass
from enum import Enum


class ServiceType(Enum):
    RESOURCE_PROVIDER = 1
    CLIENT = 2
    SOLVER = 3
    MEDIATOR = 4
    DIRECTORY = 5


@dataclass
class CID:
    """
    IPFS CID
    """

    hash: str
    data: {}

@dataclass
class Tx:
    """
    Ethereum transaction metadata
    """
    sender: str
    # how many wei
    value: float
    # method: str
    # arguments: []


@dataclass
class Service:
    service_type: ServiceType
    url: str
    # metadata will be stored as an ipfs CID
    metadata: dict
    wallet_address: str


extra_necessary_match_data = {
    "client_deposit": 5,
    "timeout": 10,
    "timeout_deposit": 3,
    "cheating_collateral_multiplier": 50,
    "price_per_instruction": 1,
}

example_offer_data = {
    "CPU": 6,
    "RAM": 3,
}

