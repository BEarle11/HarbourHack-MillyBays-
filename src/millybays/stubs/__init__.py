"""Default backend. Every stage here is a deterministic stand-in."""

from millybays.pipeline import Stages
from millybays.stubs.classifier import StubClassifier
from millybays.stubs.pricer import StubPricer
from millybays.stubs.studio import StubStudio
from millybays.stubs.writer import StubWriter

BACKEND_ID = "stub"


def stub_stages() -> Stages:
    return Stages(
        classifier=StubClassifier(),
        pricer=StubPricer(),
        writer=StubWriter(),
        studio=StubStudio(),
    )
