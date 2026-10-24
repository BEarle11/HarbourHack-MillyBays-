"""Run the four stages in order. An HTTP API can call this same function."""

from dataclasses import dataclass

from millybays.models import PipelineResult, RunContext
from millybays.ports import Classifier, Pricer, Studio, Writer


@dataclass(frozen=True)
class Stages:
    classifier: Classifier
    pricer: Pricer
    writer: Writer
    studio: Studio


def run_pipeline(ctx: RunContext, stages: Stages) -> PipelineResult:
    item = stages.classifier.classify(ctx)
    quote = stages.pricer.price(ctx, item)
    transcript = stages.writer.write(ctx, item, quote)
    ad = stages.studio.produce(ctx, item, quote, transcript)
    return PipelineResult(item=item, quote=quote, transcript=transcript, ad=ad)
