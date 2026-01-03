import dash_mantine_components as dmc
from dash import html


def data_table(
    headers: list[str],
    rows: list[list],
    row_colors: list[list[str]] | None = None,
) -> dmc.Table:
    """Create a styled data table.

    Args:
        headers: Column headers
        rows: List of row data (each row is a list of cell values)
        row_colors: Optional Mantine color names for each cell [[color, color], ...]
    """
    thead = dmc.TableThead(
        dmc.TableTr([dmc.TableTh(h) for h in headers])
    )

    tbody_rows = []
    for i, row in enumerate(rows):
        cells = []
        for j, cell in enumerate(row):
            color = None
            if row_colors and i < len(row_colors) and j < len(row_colors[i]):
                color = row_colors[i][j] or None
            cells.append(dmc.TableTd(dmc.Text(cell, c=color) if color else cell))
        tbody_rows.append(dmc.TableTr(cells))

    tbody = dmc.TableTbody(tbody_rows)

    return dmc.ScrollArea(
        dmc.Table(
            [thead, tbody],
            striped=True,
            highlightOnHover=True,
            withTableBorder=True,
            withColumnBorders=True,
        ),
        type="auto",
    )
