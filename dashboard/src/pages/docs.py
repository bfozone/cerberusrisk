import dash
from dash import dcc, callback, Output, Input
import dash_mantine_components as dmc
from pathlib import Path

dash.register_page(__name__, path="/docs", name="Documentation")

# Path to docs folder
DOCS_PATH = Path(__file__).parent.parent / "docs"

# Define doc groups with order
DOC_GROUPS = [
    {
        "label": "User Guide",
        "docs": [
            ("overview", "Overview"),
            ("getting-started", "Getting Started"),
        ],
    },
    {
        "label": "Analytics",
        "docs": [
            ("risk-metrics", "Risk Metrics"),
            ("stress-testing", "Stress Testing"),
            ("compliance", "Compliance"),
        ],
    },
    {
        "label": "Technical",
        "docs": [
            ("architecture", "Architecture"),
            ("api-reference", "API Reference"),
            ("glossary", "Glossary"),
        ],
    },
]


def layout():
    # Build tabs with group labels
    tabs_children = []

    for group in DOC_GROUPS:
        # Add group label (non-clickable)
        tabs_children.append(
            dmc.Text(
                group["label"],
                size="xs",
                fw=600,
                c="dimmed",
                style={"padding": "8px 12px 4px 12px", "textTransform": "uppercase"},
            )
        )
        # Add doc tabs for this group
        for doc_id, doc_label in group["docs"]:
            doc_path = DOCS_PATH / f"{doc_id}.md"
            if doc_path.exists():
                tabs_children.append(
                    dmc.TabsTab(doc_label, value=doc_id)
                )

    # Default to overview
    default_tab = "overview"

    return dmc.Stack(
        [
            dmc.Title("Documentation", order=2),
            dmc.Tabs(
                [
                    dmc.TabsList(tabs_children),
                ],
                id="docs-tabs",
                value=default_tab,
                variant="outline",
                orientation="horizontal",
            ),
            # Content area
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
