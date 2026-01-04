"""Local SVG icons for offline/faster loading."""

from dash import html
import base64

# SVG icon data (viewBox and path)
ICONS = {
    "nodes-down": {
        "viewBox": "0 0 16 16",
        "path": 'M13.5 11a1.5 1.5 0 1 0-3 0a1.5 1.5 0 0 0 3 0M12 14a3 3 0 1 0-.79-5.895L10.092 6.15a3 3 0 1 0-4.185 0L4.79 8.105A3.003 3.003 0 0 0 1 11a3 3 0 1 0 5.092-2.15L7.21 6.895a3 3 0 0 0 1.58 0L9.908 8.85A3 3 0 0 0 12 14m-6.5-3a1.5 1.5 0 1 0-3 0a1.5 1.5 0 0 0 3 0M8 2.5a1.5 1.5 0 1 1 0 3a1.5 1.5 0 0 1 0-3',
        "fill_rule": "evenodd",
    },
    "home": {
        "viewBox": "0 0 15 15",
        "path": 'M7.173.147a.6.6 0 0 1 .748.075l6.75 6.64l.077.093a.6.6 0 0 1-.824.838l-.095-.076l-.83-.816v5.6a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5V6.9l-.828.816a.6.6 0 0 1-.842-.855l6.75-6.64zM3 5.917V12h3V8.5l.01-.1A.5.5 0 0 1 6.5 8h3l.1.01a.5.5 0 0 1 .4.49V12h2V5.917L7.5 1.491zM7 12h2V9H7z',
    },
    "layers": {
        "viewBox": "0 0 15 15",
        "path": 'M7.146 1.49a.5.5 0 0 1 .708 0l6 5.5a.5.5 0 0 1 0 .72l-6 5.5a.5.5 0 0 1-.708 0l-6-5.5a.5.5 0 0 1 0-.72zM2.329 7.2L7.5 11.86l5.171-4.66L7.5 2.54z M.896 10.18a.5.5 0 0 1 .708-.058L7.5 15.36l5.896-5.238a.5.5 0 0 1 .666.746l-6.208 5.514a.5.5 0 0 1-.708 0L.854 10.868a.5.5 0 0 1 .042-.688',
        "fill_rule": "evenodd",
    },
    "dot-filled": {
        "viewBox": "0 0 15 15",
        "path": 'M9.875 7.5a2.375 2.375 0 1 1-4.75 0a2.375 2.375 0 0 1 4.75 0',
    },
    "mix": {
        "viewBox": "0 0 15 15",
        "path": 'M2.149 6.616a.5.5 0 0 1 .235-.666l4.5-2.25a.5.5 0 0 1 .447 0l4.5 2.25a.5.5 0 0 1-.447.894L7.5 4.96l-3.884 1.942a.5.5 0 0 1-.666-.234l-.801-.052zm5.127 1.138a.5.5 0 0 0-.447 0l-4.5 2.25a.5.5 0 0 0 .447.894L7.5 8.706l4.724 2.192a.5.5 0 0 0 .447-.894z',
        "fill_rule": "evenodd",
    },
    "sun": {
        "viewBox": "0 0 15 15",
        "path": 'M7.5 0a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2a.5.5 0 0 1 .5-.5M2.197 2.197a.5.5 0 0 1 .707 0L4.318 3.61a.5.5 0 0 1-.707.707L2.197 2.904a.5.5 0 0 1 0-.707M.5 7a.5.5 0 0 0 0 1h2a.5.5 0 0 0 0-1zM2.197 12.803a.5.5 0 0 1 0-.707L3.61 10.68a.5.5 0 1 1 .707.707l-1.414 1.415a.5.5 0 0 1-.707 0M12.5 7a.5.5 0 0 0 0 1h2a.5.5 0 0 0 0-1zm-1.818 3.682a.5.5 0 0 1 .707 0l1.414 1.414a.5.5 0 0 1-.707.707l-1.414-1.414a.5.5 0 0 1 0-.707M7.5 12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2a.5.5 0 0 1 .5-.5m2.5-4.5a2.5 2.5 0 1 1-5 0a2.5 2.5 0 0 1 5 0m1 0a3.5 3.5 0 1 1-7 0a3.5 3.5 0 0 1 7 0',
        "fill_rule": "evenodd",
    },
    "moon": {
        "viewBox": "0 0 15 15",
        "path": 'M2.9 7.5A4.6 4.6 0 0 0 7.5 12.1c1.545 0 2.932-.761 3.769-1.93a5.1 5.1 0 0 1-3.769.63a5.1 5.1 0 0 1-4.07-4.07a5.1 5.1 0 0 1 .63-3.769A4.58 4.58 0 0 0 2.9 7.5M7.5 1.9a5.6 5.6 0 1 0 0 11.2a5.6 5.6 0 0 0 0-11.2',
        "fill_rule": "evenodd",
    },
    "chevron-left": {
        "viewBox": "0 0 15 15",
        "path": 'M8.842 3.135a.5.5 0 0 1 .023.707L5.435 7.5l3.43 3.658a.5.5 0 0 1-.73.684l-3.75-4a.5.5 0 0 1 0-.684l3.75-4a.5.5 0 0 1 .707-.023',
        "fill_rule": "evenodd",
    },
    "chevron-right": {
        "viewBox": "0 0 15 15",
        "path": 'M6.158 3.135a.5.5 0 0 1 .707.023l3.75 4a.5.5 0 0 1 0 .684l-3.75 4a.5.5 0 1 1-.73-.684L9.566 7.5l-3.43-3.658a.5.5 0 0 1 .023-.707',
        "fill_rule": "evenodd",
    },
    "cross-1": {
        "viewBox": "0 0 15 15",
        "path": 'M11.782 4.032a.575.575 0 1 0-.813-.814L7.5 6.687L4.032 3.218a.575.575 0 0 0-.814.814L6.687 7.5l-3.469 3.468a.575.575 0 0 0 .814.814L7.5 8.313l3.469 3.469a.575.575 0 0 0 .813-.814L8.313 7.5z',
        "fill_rule": "evenodd",
    },
    "hamburger-menu": {
        "viewBox": "0 0 15 15",
        "path": 'M1.5 3a.5.5 0 0 0 0 1h12a.5.5 0 0 0 0-1zm0 4a.5.5 0 0 0 0 1h12a.5.5 0 0 0 0-1zm0 4a.5.5 0 0 0 0 1h12a.5.5 0 0 0 0-1z',
        "fill_rule": "evenodd",
    },
}


def _make_svg(name, color="currentColor"):
    """Generate SVG string for an icon."""
    icon = ICONS[name]
    fill_rule = icon.get("fill_rule", "")
    fill_rule_attr = f' fill-rule="{fill_rule}" clip-rule="{fill_rule}"' if fill_rule else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{icon["viewBox"]}" width="100%" height="100%"><path fill="{color}"{fill_rule_attr} d="{icon["path"]}"/></svg>'


def _svg_to_data_uri(svg_string):
    """Convert SVG string to data URI."""
    encoded = base64.b64encode(svg_string.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


def Icon(name, size=18, color=None, className="", id=None, **kwargs):
    """
    Render a local SVG icon as an img element.

    Args:
        name: Icon name (e.g., 'home', 'layers')
        size: Icon size in pixels (default 18)
        color: Hex color (e.g., '#a78bfa'). If None, uses default dark color.
        className: Additional CSS classes
        id: Optional element ID
    """
    if name not in ICONS:
        raise ValueError(f"Unknown icon: {name}. Available: {list(ICONS.keys())}")

    # Default color if not specified
    icon_color = color or "#e4e4e7"  # Light gray that works on dark bg

    svg = _make_svg(name, icon_color)
    src = _svg_to_data_uri(svg)

    style = {
        "width": f"{size}px",
        "height": f"{size}px",
        "display": "inline-block",
        "verticalAlign": "middle",
        "flexShrink": "0",
    }

    # Merge with any additional styles
    if "style" in kwargs:
        style.update(kwargs.pop("style"))

    props = {
        "src": src,
        "className": f"icon icon-{name} {className}".strip(),
        "style": style,
        **kwargs,
    }
    if id:
        props["id"] = id

    return html.Img(**props)
