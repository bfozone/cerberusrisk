from dash import html
import dash_bootstrap_components as dbc


def data_table(
    headers: list[str],
    rows: list[list],
    row_classes: list[list[str]] | None = None,
    size: str | None = None,
) -> dbc.Table:
    """Create a styled data table.

    Args:
        headers: Column headers
        rows: List of row data (each row is a list of cell values)
        row_classes: Optional CSS classes for each cell [[class, class], ...]
        size: Table size ('sm' for small)
    """
    thead = html.Thead(html.Tr([html.Th(h) for h in headers]))

    tbody_rows = []
    for i, row in enumerate(rows):
        cells = []
        for j, cell in enumerate(row):
            class_name = ""
            if row_classes and i < len(row_classes) and j < len(row_classes[i]):
                class_name = row_classes[i][j] or ""
            cells.append(html.Td(cell, className=class_name) if class_name else html.Td(cell))
        tbody_rows.append(html.Tr(cells))

    tbody = html.Tbody(tbody_rows)

    return dbc.Table(
        [thead, tbody],
        bordered=True,
        hover=True,
        responsive=True,
        size=size,
        className="table-dark",
    )
