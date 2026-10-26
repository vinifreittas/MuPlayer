from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from muplayer.infrastructure.logging import setup_logging
from muplayer.interface.cli.commands.log import _filter_log_content
from muplayer.main import _validate_environment, cli

runner = CliRunner()

SAMPLE_LOG = """[2026-10-26 10:00:00] INFO     [muplayer.main:100] Application starting
[2026-10-26 10:00:01] DEBUG    [muplayer.infra:42] Cache miss for key: track_123
Traceback (debug detail):
  at line 42 in infra.py
[2026-10-26 10:00:02] WARNING  [muplayer.audio:50] Engine latency high
[2026-10-26 10:00:03] ERROR    [muplayer.player:88] Failed to play stream
Traceback (most recent call last):
  File "player.py", line 88, in play
ValueError: Stream broken
[2026-10-26 10:00:04] DEBUG    [muplayer.cleanup:12] Cleaning temp buffers
"""


SAMPLE_JSONL_LOG = (
    '{"timestamp": "2026-10-26 10:00:00", "level": "INFO", "name": "muplayer.main", "lineno": 100, "message": "Application starting"}\n'
    '{"timestamp": "2026-10-26 10:00:01", "level": "DEBUG", "name": "muplayer.infra", "lineno": 42, "message": "Cache miss for key: track_123"}\n'
    '{"timestamp": "2026-10-26 10:00:02", "level": "WARNING", "name": "muplayer.audio", "lineno": 50, "message": "Engine latency high"}\n'
    '{"timestamp": "2026-10-26 10:00:03", "level": "ERROR", "name": "muplayer.player", "lineno": 88, "message": "Failed to play stream", "exception": "Traceback (most recent call last):\\n  File \\"player.py\\", line 88\\nValueError: Stream broken"}\n'
    '{"timestamp": "2026-10-26 10:00:04", "level": "DEBUG", "name": "muplayer.cleanup", "lineno": 12, "message": "Cleaning temp buffers"}\n'
)


def test_filter_log_content_jsonl_without_debug():
    """Valida se _filter_log_content descarta JSONL DEBUG e formata INFO/WARN/ERROR com exception."""
    filtered = _filter_log_content(SAMPLE_JSONL_LOG, include_debug=False)

    assert "Application starting" in filtered
    assert "Engine latency high" in filtered
    assert "Failed to play stream" in filtered
    assert "ValueError: Stream broken" in filtered

    # DEBUG entries must be filtered out
    assert "Cache miss for key: track_123" not in filtered
    assert "Cleaning temp buffers" not in filtered


def test_filter_log_content_jsonl_with_debug():
    """Valida se _filter_log_content com include_debug=True inclui registros DEBUG."""
    filtered = _filter_log_content(SAMPLE_JSONL_LOG, include_debug=True)

    assert "Application starting" in filtered
    assert "Cache miss for key: track_123" in filtered
    assert "Cleaning temp buffers" in filtered


def test_filter_log_content_legacy_plaintext_fallback():
    """Valida retrocompatibilidade com logs legados em texto plano."""
    filtered = _filter_log_content(
        "[2026-10-26 10:00:00] INFO     [mod:1] info msg\n[2026-10-26 10:00:01] DEBUG    [mod:2] debug msg",
        include_debug=False,
    )
    assert "info msg" in filtered
    assert "debug msg" not in filtered


def test_cli_root_rejects_debug_and_force():
    """Garante que as flags --debug e --force foram removidas do CLI raiz e são rejeitadas."""
    res_debug = runner.invoke(cli, ["--debug"])
    assert res_debug.exit_code != 0
    assert "no such option" in res_debug.output.lower() or "unknown option" in res_debug.output.lower()

    res_force = runner.invoke(cli, ["--force"])
    assert res_force.exit_code != 0
    assert "no such option" in res_force.output.lower() or "unknown option" in res_force.output.lower()


def test_cli_root_help_does_not_list_debug_or_force():
    """Garante que --debug e --force não aparecem no --help do comando raiz."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--debug" not in result.output
    assert "--force" not in result.output


def test_cli_log_no_logs_found(tmp_path):
    """Valida saída de erro amigável quando nenhum arquivo de log existe."""
    with patch("muplayer.interface.cli.commands.log.get_log_dir", return_value=tmp_path):
        result = runner.invoke(cli, ["log"])
        assert result.exit_code == 1
        assert "No log files found." in result.output


def test_cli_log_filtering_integration(tmp_path):
    """Valida filtragem no comando 'muplayer log' com e sem a flag --debug em arquivos JSONL."""
    log_file = tmp_path / "app-2026-10-26_10-00-00.log"
    log_file.write_text(SAMPLE_JSONL_LOG, encoding="utf-8")

    with patch("muplayer.interface.cli.commands.log.get_log_dir", return_value=tmp_path):
        # 1. Padrão: sem --debug (filtra mensagens DEBUG)
        res_default = runner.invoke(cli, ["log"])
        assert res_default.exit_code == 0
        assert "Application starting" in res_default.output
        assert "Failed to play stream" in res_default.output
        assert "Cache miss for key" not in res_default.output

        # 2. Com --debug: inclui tudo
        res_debug = runner.invoke(cli, ["log", "--debug"])
        assert res_debug.exit_code == 0
        assert "Application starting" in res_debug.output
        assert "Cache miss for key" in res_debug.output

        # 3. Com flag curta -d: inclui tudo
        res_short = runner.invoke(cli, ["log", "-d"])
        assert res_short.exit_code == 0
        assert "Cache miss for key" in res_short.output


def test_cli_log_invalid_index(tmp_path):
    """Valida tratamento de índices de log inválidos ou fora do intervalo."""
    log_file = tmp_path / "app-2026-10-26_10-00-00.log"
    log_file.write_text(SAMPLE_JSONL_LOG, encoding="utf-8")

    with patch("muplayer.interface.cli.commands.log.get_log_dir", return_value=tmp_path):
        # Índice 0 (fora do range 1..5)
        res_zero = runner.invoke(cli, ["log", "0"])
        assert res_zero.exit_code == 1
        assert "Invalid index 0" in res_zero.output

        # Índice maior do que a quantidade de logs existentes
        res_overflow = runner.invoke(cli, ["log", "2"])
        assert res_overflow.exit_code == 1
        assert "Log #2 does not exist" in res_overflow.output


def test_validate_environment_checks():
    """Valida pre-flight checks em _validate_environment sem o parâmetro force."""
    import typer

    # Falha quando não há motores de áudio
    with pytest.raises(typer.Exit):
        _validate_environment(
            engines={"mpv": None, "vlc": None},
            check_terminal=lambda: (True, None),
            detect_js=lambda: True,
        )

    # Falha quando terminal não é compatível
    with pytest.raises(typer.Exit):
        _validate_environment(
            engines={"mpv": "/path/libmpv.so", "vlc": None},
            check_terminal=lambda: (False, "Non-interactive dumb terminal"),
            detect_js=lambda: True,
        )

    # Falha quando JS runtime não é encontrado
    with pytest.raises(typer.Exit):
        _validate_environment(
            engines={"mpv": "/path/libmpv.so", "vlc": None},
            check_terminal=lambda: (True, None),
            detect_js=lambda: False,
        )

    # Sucesso quando tudo está presente
    _validate_environment(
        engines={"mpv": "/path/libmpv.so", "vlc": None},
        check_terminal=lambda: (True, None),
        detect_js=lambda: True,
    )


def test_setup_logging_emits_jsonl(tmp_path):
    """Valida se setup_logging grava entradas estruturadas em JSON Lines."""
    import json

    logger = setup_logging(log_dir=tmp_path)
    logger.info("Test info message")
    logger.debug("Test debug message")

    log_files = list(tmp_path.glob("app-*.log"))
    assert len(log_files) == 1

    lines = log_files[0].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 2

    # Verifica se cada linha é um JSON válido com os campos esperados
    records = [json.loads(line) for line in lines]
    assert any(r["level"] == "INFO" and "Test info message" in r["message"] for r in records)
    assert any(r["level"] == "DEBUG" and "Test debug message" in r["message"] for r in records)
