from pathlib import Path
from typing import Any

from muplayer.infrastructure.system import get_data_dir


def get_tortoise_config(db_path: Path | None = None) -> dict[str, Any]:
    resolved_path = db_path.resolve() if db_path else (get_data_dir() / "muplayer.db").resolve()
    models_list = ["muplayer.infrastructure.database.tables"]
    try:
        import aerich  # noqa: F401

        models_list.append("aerich.models")
    except ImportError:
        pass

    return {
        "connections": {"default": f"sqlite://{resolved_path}"},
        "apps": {
            "models": {
                "models": models_list,
                "default_connection": "default",
            }
        },
    }


TORTOISE_ORM = get_tortoise_config()
