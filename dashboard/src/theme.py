import dash_mantine_components as dmc

# Neo Purple Extended - Dark palette
PALETTE_DARK = {
    # Core surfaces
    "background": "#0d0d12",
    "backgroundAlt": "#0a0a0e",
    "surface": "#1a1a24",
    "surfaceHover": "#22222e",
    "surfaceActive": "#2a2a38",
    "border": "#2d2d3a",
    "borderSubtle": "#232330",
    # Brand
    "primary": "#a78bfa",
    "primaryHover": "#c084fc",
    "secondary": "#22d3ee",
    "secondaryHover": "#67e8f9",
    # Semantic
    "positive": "#4ade80",
    "negative": "#fb7185",
    "warning": "#fbbf24",
    "info": "#60a5fa",
    # Text
    "text": "#ffffff",
    "textSecondary": "#c8c8d8",
    "muted": "#9898a8",
    "disabled": "#5a5a68",
}

# Neo Purple Extended - Light palette
PALETTE_LIGHT = {
    # Core surfaces
    "background": "#faf9fb",
    "backgroundAlt": "#f5f3f7",
    "surface": "#ffffff",
    "surfaceHover": "#f8f7fa",
    "surfaceActive": "#f0eef3",
    "border": "#e9e5f0",
    "borderSubtle": "#f0edf5",
    # Brand
    "primary": "#7c3aed",
    "primaryHover": "#6d28d9",
    "secondary": "#0891b2",
    "secondaryHover": "#0e7490",
    # Semantic
    "positive": "#16a34a",
    "negative": "#e11d48",
    "warning": "#d97706",
    "info": "#2563eb",
    # Text
    "text": "#1e1b2e",
    "textSecondary": "#4a4760",
    "muted": "#6b6880",
    "disabled": "#a8a5b8",
}

# Brand color scales
PURPLE_SCALE = [
    "#faf5ff",  # 50
    "#f3e8ff",  # 100
    "#e9d5ff",  # 200
    "#d8b4fe",  # 300
    "#c084fc",  # 400
    "#a855f7",  # 500
    "#9333ea",  # 600
    "#7c3aed",  # 700
    "#6b21a8",  # 800
    "#581c87",  # 900
]

CYAN_SCALE = [
    "#ecfeff",  # 50
    "#cffafe",  # 100
    "#a5f3fc",  # 200
    "#67e8f9",  # 300
    "#22d3ee",  # 400
    "#06b6d4",  # 500
    "#0891b2",  # 600
    "#0e7490",  # 700
    "#155e75",  # 800
    "#164e63",  # 900
]

# Semantic color scales
POSITIVE_SCALE = [
    "#f0fdf4", "#dcfce7", "#bbf7d0", "#86efac", "#4ade80",
    "#22c55e", "#16a34a", "#15803d", "#166534", "#14532d",
]

NEGATIVE_SCALE = [
    "#fff1f2", "#ffe4e6", "#fecdd3", "#fda4af", "#fb7185",
    "#f43f5e", "#e11d48", "#be123c", "#9f1239", "#881337",
]

WARNING_SCALE = [
    "#fffbeb", "#fef3c7", "#fde68a", "#fcd34d", "#fbbf24",
    "#f59e0b", "#d97706", "#b45309", "#92400e", "#78350f",
]

INFO_SCALE = [
    "#eff6ff", "#dbeafe", "#bfdbfe", "#93c5fd", "#60a5fa",
    "#3b82f6", "#2563eb", "#1d4ed8", "#1e40af", "#1e3a8a",
]

# Sequential scales for heatmaps
SEQUENTIAL = {
    "purpleIntensity": [
        "#1a1a24", "#2d2348", "#4a2c7a", "#6b35a8", "#8b3fd6",
        "#a855f7", "#c084fc", "#d8b4fe", "#e9d5ff",
    ],
    "cyanIntensity": [
        "#0d1a1f", "#0c3340", "#0e4d60", "#0f6680", "#0891b2",
        "#22d3ee", "#67e8f9", "#a5f3fc", "#cffafe",
    ],
    "heat": [
        "#1a1a24", "#2d1f3d", "#4a1f55", "#7c1d5d", "#a8184a",
        "#d91a3c", "#f43f3f", "#fb7f4c", "#fbbf24",
    ],
    "cool": [
        "#0d0d12", "#0d1825", "#0e2638", "#0f354d", "#0e4d6a",
        "#0891b2", "#22d3ee", "#67e8f9", "#a5f3fc",
    ],
}

# Diverging scales for +/- values
DIVERGING = {
    "redPurpleCyan": [
        "#e11d48", "#f43f5e", "#fb7185", "#8b8b9a",
        "#a78bfa", "#22d3ee", "#06b6d4",
    ],
    "lossGain": [
        "#e11d48", "#f43f5e", "#fb7185", "#fda4af", "#6b6b78",
        "#86efac", "#4ade80", "#22c55e", "#16a34a",
    ],
    "performance": [
        "#881337", "#be123c", "#f43f5e", "#6b6b78",
        "#4ade80", "#22c55e", "#15803d",
    ],
}

# Categorical colors for charts
CATEGORICAL = {
    "primary": [
        "#a78bfa", "#22d3ee", "#4ade80", "#fbbf24",
        "#fb7185", "#60a5fa", "#f472b6", "#34d399",
    ],
    "muted": [
        "#6b5b95", "#2a8a9e", "#3a9a5e", "#a8892e",
        "#a85670", "#4070b0", "#9e5080", "#2a8a70",
    ],
    "assetClasses": {
        "equity": "#a78bfa",
        "fixedIncome": "#22d3ee",
        "commodities": "#fbbf24",
        "realEstate": "#f472b6",
        "cash": "#6b7280",
        "alternatives": "#34d399",
        "derivatives": "#60a5fa",
        "crypto": "#fb7185",
    },
}

# Default palette reference
PALETTE = PALETTE_DARK

# Semantic aliases (for backwards compatibility)
COLORS = {
    "positive": PALETTE["positive"],
    "negative": PALETTE["negative"],
    "warning": PALETTE["warning"],
    "info": PALETTE["info"],
    "muted": PALETTE["muted"],
}

# Mantine theme configuration
theme = dmc.DEFAULT_THEME.copy()
theme.update({
    "primaryColor": "violet",
    "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "fontFamilyMonospace": "'JetBrains Mono', 'Fira Code', monospace",
    "defaultRadius": "md",
    "colors": {
        "violet": PURPLE_SCALE,
        "cyan": CYAN_SCALE,
    },
})


def get_palette(scheme: str = "dark") -> dict:
    """Get palette for the given color scheme."""
    return PALETTE_DARK if scheme == "dark" else PALETTE_LIGHT


def get_color(value: float, threshold: float = 0, scheme: str = "dark") -> str:
    """Return color based on value (positive=green, negative=red)."""
    palette = get_palette(scheme)
    return palette["positive"] if value >= threshold else palette["negative"]
