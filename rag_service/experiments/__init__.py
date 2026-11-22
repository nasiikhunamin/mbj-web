"""Experiment orchestration: batch runner (Task 4.1) and dashboard data (Task 3.6)."""

from rag_service.experiments.dashboard import (
    EXPERIMENT_CODES,
    SOURCE_TYPES,
    available_values,
    build_item_table,
    filter_items,
    load_answers,
    load_details,
    load_ground_truth,
    load_summary,
    metric_means,
)
from rag_service.experiments.runner import (
    RunnerError,
    build_payload,
    build_record,
    load_questions,
    run_all,
    run_experiment,
    write_payload,
)

__all__ = [
    "EXPERIMENT_CODES",
    "SOURCE_TYPES",
    "RunnerError",
    "available_values",
    "build_item_table",
    "filter_items",
    "load_answers",
    "load_details",
    "load_ground_truth",
    "load_summary",
    "metric_means",
    "build_payload",
    "build_record",
    "load_questions",
    "run_all",
    "run_experiment",
    "write_payload",
]
