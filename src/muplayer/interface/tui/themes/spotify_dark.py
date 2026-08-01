from textual.theme import Theme

spotify_dark_theme = Theme(
    name="spotify-dark",
    primary="#1DB954",
    secondary="#1ED760",
    foreground="#FFFFFF",
    background="#000000",
    success="#1DB954",
    warning="#F1C40F",
    error="#E74C3C",
    surface="#121212",
    panel="#242424",
    dark=True,
    variables={
        "text-muted": "#B3B3B3",
        "block-cursor-text-style": "none",
    },
)
