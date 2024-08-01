"""Provide basic test configuration and fixture root."""

from io import TextIOWrapper
from pathlib import Path

import pytest
import requests_mock


def pytest_addoption(parser):
    parser.addoption("--performance", action="store_true", help="Run performance tests")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--performance"):
        return
    skip_custom = pytest.mark.skip(reason="Need --performance option to run")
    for item in items:
        if "performance" in item.keywords:
            item.add_marker(skip_custom)


@pytest.fixture(scope="session")
def fixtures_dir():
    """Provide path to fixtures directory."""
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def schema(fixtures_dir):
    with (fixtures_dir / "introspection_response.json").open() as f:
        return f.read()


@pytest.fixture(scope="session")
def set_up_graphql_mock(schema: str):
    def _set_up_graphql_mock(m: requests_mock.Mocker, json_response: TextIOWrapper):
        """Initialize mock for a new set of GraphQL requests.

        The client will first ping the server for a schema, and then send a request that
        has been validated against that schema. This method ensures that Mockers are called
        in the correct way to handle this (counterintuitively, we first set the test-specific
        response and then, secondly, add a listener with a custom match pattern for the
        schema response).

        :param m: mock requests object
        :param schema_response: schema description for introspection/query validation
        :param json_response: expected query response from the server
        """
        m.post(
            "https://dgidb.org/api/graphql",
            text=json_response.read(),
        )
        m.post(
            "https://dgidb.org/api/graphql",
            additional_matcher=lambda r: "IntrospectionQuery"
            in r.json().get("query", ""),
            text=schema,
        )

    return _set_up_graphql_mock
