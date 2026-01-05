import dash
from dash import dcc, callback, Output, Input
import dash_mantine_components as dmc
from pathlib import Path

dash.register_page(__name__, path="/docs", name="Documentation")

# Path to docs folder
DOCS_PATH = Path(__file__).parent.parent / "docs"


def get_doc_files():
    """Get all markdown files from docs folder."""
    if not DOCS_PATH.exists():
        return []
    return sorted(DOCS_PATH.glob("*.md"))


def file_to_tab_label(filepath: Path) -> str:
    """Convert filename to readable tab label."""
    # overview.md -> Overview, risk-metrics.md -> Risk Metrics
    name = filepath.stem.replace("-", " ").replace("_", " ")
    return name.title()


def layout():
    doc_files = get_doc_files()

    if not doc_files:
        return dmc.Stack([
            dmc.Title("Documentation", order=2),
            dmc.Alert("No documentation files found.", color="yellow"),
        ])

    # Create tabs from markdown files
    tabs_list = [
        dmc.TabsTab(file_to_tab_label(f), value=f.stem)
        for f in doc_files
    ]

    # Default to first file
    default_tab = doc_files[0].stem

    return dmc.Stack(
        [
            dmc.Title("Documentation", order=2),
            dmc.Tabs(
                [
                    dmc.TabsList(tabs_list),
                ],
                id="docs-tabs",
                value=default_tab,
                variant="outline",
            ),
            # Content area outside tabs - updates via callback
            dcc.Loading(
                dmc.Paper(
                    dcc.Markdown(
                        id="docs-content",
                        className="markdown-body",
                        mathjax=True,
                    ),
                    p="md",
                    radius="md",
                    withBorder=True,
                ),
                type="dot",
            ),
        ],
        gap="md",
    )


@callback(
    Output("docs-content", "children"),
    Input("docs-tabs", "value"),
)
def render_doc_content(tab_value):
    """Load markdown content based on selected tab."""
    if not tab_value:
        return "Select a topic from the tabs above."

    doc_file = DOCS_PATH / f"{tab_value}.md"

    if not doc_file.exists():
        return f"Documentation file not found: {tab_value}.md"

    try:
        content = doc_file.read_text(encoding="utf-8")
        return content
    except Exception as e:
        return f"Error loading documentation: {e}"
