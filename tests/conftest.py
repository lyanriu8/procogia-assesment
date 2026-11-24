import pytest

from contradiction_lab.config import Settings
from contradiction_lab.fixtures import FixtureCorpus
from contradiction_lab.graph import ResearchEngine


@pytest.fixture
def corpus():
    return FixtureCorpus()


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path)


@pytest.fixture
def engine(settings):
    return ResearchEngine(settings)
