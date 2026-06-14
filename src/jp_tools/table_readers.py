"""Pluggable table reader objects for jp_tools pipelines."""

import re
from abc import ABC, abstractmethod

import pandas as pd


class TableReader(ABC):
    @abstractmethod
    def read(self) -> pd.DataFrame: ...


class CsvTableReader(TableReader):
    def __init__(self, path: str):
        self.path = path

    def read(self) -> pd.DataFrame:
        return pd.read_csv(self.path)


class ClipboardHtmlTableReader(TableReader):
    def read(self) -> pd.DataFrame:
        import win32clipboard

        win32clipboard.OpenClipboard()
        try:
            html_format = win32clipboard.RegisterClipboardFormat("HTML Format")
            if not win32clipboard.IsClipboardFormatAvailable(html_format):
                raise RuntimeError("No HTML table found in clipboard.")
            html = win32clipboard.GetClipboardData(html_format)
        finally:
            win32clipboard.CloseClipboard()

        html = html.decode("utf-8", errors="ignore")
        html = re.sub(r"data:[^;]+;base64,[A-Za-z0-9+/=]+", "", html)

        tables = pd.read_html(html)
        if not tables:
            raise ValueError("No table found in clipboard HTML.")
        df = tables[0]
        df.columns = [str(c).strip() for c in df.columns]
        return df.map(lambda x: x.strip() if isinstance(x, str) else x)
