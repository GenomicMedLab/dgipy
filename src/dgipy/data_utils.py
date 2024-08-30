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


def drop_none_attrs(column: list[dict]) -> list[dict]:
    """For an attributes column (i.e., a list of dicts), drop all entries with `None`
    values.

    In DGIdb (and consequently DGIpy), there's no semantic information intended by
    giving attributes `None` values. They are, however, included to ensure compatibility
    with strongly-structured dataframe libraries like Polars. Otherwise, these
    properties are unnecessary, and can be safely dropped without loss of information.

    >>> from dgipy import get_interactions
    >>> from dgipy.data_utils import drop_none_attrs
    >>> results = get_interactions(["braf"])
    >>> results["interaction_attributes"][2]
    {'Response Type': None, 'Combination Therapy': None, 'Novel Drug Target': ['Established target'], 'Variant Effect': None, 'Cancer Type': None, 'Direct Interaction': None, 'Indication': None, 'Clinical Trial Name': ['XL281'], 'Pathway': None, 'Clinical Trial ID': None, 'Mechanism of Action': None, 'Evidence Type': None, 'Alteration': None, 'Approval Status': None}
    >>> results["interaction_attributes"] = drop_none_attrs(
    ...     results["interaction_attributes"]
    ... )
    >>> results["interaction_attributes"][2]
    {'Novel Drug Target': ['Established target'], 'Clinical Trial Name': ['XL281']}

    :param column: an individual column value from the columnar output of a
        :py:module:`dgipy.dgidb` query function
    :return: the same column, but with `None` attributes removed from all cells
    """
    return [{k: v for k, v in d.items() if v is not None} for d in column]
