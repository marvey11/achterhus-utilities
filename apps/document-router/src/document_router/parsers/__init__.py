from .base import BaseDocumentParser
from .naturstrom import NaturstromParser
from .ryd import RydParser
from .scalable import ScalableParser
from .vodafone import VodafoneParser

PARSER_LIST: list[type[BaseDocumentParser]] = [
    NaturstromParser,
    RydParser,
    ScalableParser,
    VodafoneParser,
]

__all__ = [
    "PARSER_LIST",
    "BaseDocumentParser",
    "NaturstromParser",
    "RydParser",
    "ScalableParser",
    "VodafoneParser",
]
