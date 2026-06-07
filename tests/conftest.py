import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that require network access, yt-dlp, ffmpeg, and the ASR model.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: requires network access and heavy deps (yt-dlp, ffmpeg, ASR model)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--integration"):
        return
    skip = pytest.mark.skip(reason="pass --integration to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)
