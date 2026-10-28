import pytest
from textual.app import App, ComposeResult
from textual.widgets import Select

from muplayer.domain import AppConfig
from muplayer.interface.tui.modals.configurations.configurations import Configurations


class DummyApp(App[None]):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config

    def compose(self) -> ComposeResult:
        yield from ()


@pytest.mark.asyncio
async def test_configurations_modal_lists_themes_and_selects_current():
    config = AppConfig(theme="nord")
    app = DummyApp(config)
    async with app.run_test() as pilot:
        modal = Configurations(config=config)
        dismiss_result = None

        def on_dismiss(result):
            nonlocal dismiss_result
            dismiss_result = result

        app.push_screen(modal, on_dismiss)
        await pilot.pause()

        theme_select = modal.query_one("#config-theme", Select)
        assert theme_select.value == "nord"

        # Verify themes listed come dynamically from app.available_themes
        available_theme_names = set(app.available_themes.keys())
        options_values = {val for _, val in theme_select._options if val not in (Select.BLANK, Select.NULL)}
        assert options_values == available_theme_names

        # Change theme and dismiss
        theme_select.value = "dracula"
        modal.action_dismiss()
        await pilot.pause()

        assert dismiss_result is not None
        assert dismiss_result["theme"] == "dracula"
