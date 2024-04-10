"""
Markdown table utility functions.
"""

import re
from contextlib import contextmanager
from pathlib import Path

from openpyxl import Workbook

from tests.utils.utils import get_temp_dir


def _strp_cell(cell):
    val = cell.strip()
    if val == "":
        return None
    val = val.replace(r"\|", "|")
    return val


def _extract_array(mdtablerow):
    match = re.match(r"\s*\|(.*)\|\s*", mdtablerow)
    if match:
        mtchstr = match.groups()[0]
        if re.match(r"^[\|-]+$", mtchstr):
            return False
        else:
            return [_strp_cell(c) for c in re.split(r"(?<!\\)\|", mtchstr)]

    return False


def _is_null_row(r_arr):
    for cell in r_arr:
        if cell is not None:
            return False

    return True


def md_table_to_ss_structure(mdstr: str) -> list[tuple[str, list[list[str]]]]:
    ss_arr = []
    for item in mdstr.split("\n"):
        arr = _extract_array(item)
        if arr:
            ss_arr.append(arr)
    sheet_name = False
    sheet_arr = False
    sheets = []
    for row in ss_arr:
        if row[0] is not None:
            if sheet_arr:
                sheets.append((sheet_name, sheet_arr))
            sheet_arr = []
            sheet_name = row[0]
        excluding_first_col = row[1:]
        if sheet_name and not _is_null_row(excluding_first_col):
            sheet_arr.append(excluding_first_col)
    sheets.append((sheet_name, sheet_arr))

    return sheets


def md_table_to_workbook(mdstr: str) -> Workbook:
    """
    Convert Markdown table string to an openpyxl.Workbook. Call wb.save() to persist.
    """
    md_data = md_table_to_ss_structure(mdstr=mdstr)
    wb = Workbook(write_only=True)
    for key, rows in md_data:
        sheet = wb.create_sheet(title=key)
        for r in rows:
            sheet.append(r)
    return wb


@contextmanager
def md_table_to_temp_dir(form_id: str, mdstr: str) -> Path:
    """
    Convert MarkDown table string to a XLSX file saved in a temp directory.

    :param form_id: The xmlFormId of the Form being referenced.
    :param mdstr: The MarkDown table string.
    :return: The path of the XLSX file.
    """
    with get_temp_dir() as td:
        fp = Path(td) / f"{form_id}.xlsx"
        md_table_to_workbook(mdstr).save(fp.as_posix())
        yield fp
