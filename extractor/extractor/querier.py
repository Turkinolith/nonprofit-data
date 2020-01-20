from __future__ import annotations
from defusedxml import ElementTree
from logging import getLogger
from typing import Dict, Optional, TextIO


_logger = getLogger(__name__)


class Querier:
    """
    A Querier is a helper for extracting data from a filing XML file. It
    provides helper methods for getting typed data using XPaths.

    >>> querier = Querier.from_path("fixtures/filing.xml")
    >>> querier.find_str("/IRS990/FormationYr")
    '2004'
    >>> querier.find_int("/IRS990/TotalEmployeeCnt")
    19
    """

    _namespaces: Dict[str, str]

    _tree: ElementTree

    @staticmethod
    def from_path(xml_path: str) -> Querier:
        """
        A factory primarily intended for testing and interactive (REPL or
        Jupyter) use.
        """
        _logger.debug(f"create querier for '{xml_path}'")
        with open(xml_path) as xmlFile:
            return Querier.from_file(xmlFile)

    @staticmethod
    def from_file(xml_file: TextIO) -> Querier:
        """
        The standard factory which accepts a file-like object.
        """
        content = xml_file.read()

        # The XML files seem to come back with some kind of unicode identifier
        # sequence at the beginning and Python's XML processing barfs on it. So
        # here we strip it off to make sure that "<" (opening bracket for the
        # doctype) is the first character.
        while not content.startswith("<"):
            content = content[1:]

        byteContent = content.encode("utf-8")
        _logger.info(f"hydrate querier: '{str(byteContent[:40])}'")

        tree = ElementTree.fromstring(byteContent)

        return Querier(tree)

    def __init__(self, tree: ElementTree):
        self._namespaces = {
            "efile": "http://www.irs.gov/efile",
        }
        self._tree = tree

    def find_float(self, path: str) -> Optional[float]:
        """
        Extract a field from the XML document adn convert
        it to a float before returning it.
        """
        _logger.debug(f"find float at '{path}'")

        rawValue = self.find_str(path)
        _logger.debug(f"found float - '{rawValue}'")

        if rawValue is None:
            return None

        return float(rawValue)

    def find_int(self, path: str) -> Optional[int]:
        """
        Extract a field from the XML document and
        convert it to an integer before returning it.
        """
        _logger.debug(f"find int at '{path}'")

        rawValue = self.find_str(path)
        _logger.debug(f"found int - '{rawValue}'")

        if rawValue is None:
            return None

        return int(rawValue)

    def find_str(self, path: str) -> Optional[str]:
        """
        Extract a field from the XML document and return
        it exactly as it was contained in the document.
        """
        _logger.debug(f"find str at '{path}'")

        fullPath = self._add_namespace(path)
        _logger.debug(f"find str at '{fullPath}'")

        element = self._tree.find(fullPath, namespaces=self._namespaces)

        if element is None:
            _logger.debug(f"found str - '{None}'")
            return None

        _logger.debug(f"found str - '{element.text}'")
        return element.text

    def _add_namespace(self, path: str) -> str:
        """
        Add the default namespace to all path segments
        that do not already have one.
        """
        segments = ["efile:ReturnData"] + [
            f"efile:{tag}" for tag in path.lstrip("/").split("/")
        ]
        fullPath = "/".join(segments)
        return fullPath
