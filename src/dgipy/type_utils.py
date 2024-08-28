"""Provide utilities relating to data types."""


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
