"""PipelineJudge — evaluate multi-agent AI pipelines.

Quick start:
    from pipelinejudge import evaluate

    result = evaluate(
        query="What is the refund policy?",
        steps=[
            {"name": "classifier", "output": {"intent": "refund_inquiry"}},
            {"name": "retriever", "output": {"chunks": [...]}},
            {"name": "generator", "output": {"answer": "Our policy allows..."}},
        ]
    )
"""

from sdk.evaluate import evaluate

__all__ = ["evaluate"]
__version__ = "1.0.0"
