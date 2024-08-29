"""Provide utilities relating to data types."""

import csv
from pathlib import Path


def make_tabular(columnar_dict: dict) -> list[dict]:
    """Convert DGIpy query method output to a tabular format.

    :param columnar_dict: column-oriented dict as returned by DGIpy query methods
    :return: list of table rows, where each row keys the column name to the value at
    that column and row.
    """
    return [
        dict(zip(columnar_dict.keys(), row, strict=False))
        for row in zip(*columnar_dict.values(), strict=False)
    ]


def dump_columnar_to_tsv(columnar_dict: dict, output_file: Path) -> None:
    """Dump DGIpy query method output to a TSV file.

    :param columnar_dict: column-oriented dict as returned by DGIpy query methods
    :param output_file: path to save location
    """
    rows = zip(*columnar_dict.values(), strict=False)
    with output_file.open("w", newline="") as tsvfile:
        writer = csv.writer(tsvfile, delimiter="\t")
        writer.writerow(columnar_dict.keys())
        writer.writerows(rows)
