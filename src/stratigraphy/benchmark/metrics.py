"""Classes for keeping track of metrics such as the F1-score, precision and recall."""

from collections import defaultdict
from collections.abc import Callable

import pandas as pd
from stratigraphy.evaluation.evaluation_dataclasses import Metrics


class DatasetMetrics:
    """Keeps track of a particular metrics for all documents in a dataset."""

    # TODO: Currently, some methods for averaging metrics are in the Metrics class.
    # (see micro_average(metric_list: list["Metrics"]). On the long run, we should refactor
    # this to have a single place where these averaging computations are implemented.

    def __init__(self):
        self.metrics: dict[str, Metrics] = {}

    def macro_f1(self) -> float:
        """Compute the macro F1 score."""
        if self.metrics:
            return sum([metric.f1 for metric in self.metrics.values()]) / len(self.metrics)
        else:
            return 0

    def macro_precision(self) -> float:
        """Compute the macro precision score."""
        if self.metrics:
            return sum([metric.precision for metric in self.metrics.values()]) / len(self.metrics)
        else:
            return 0

    def macro_recall(self) -> float:
        """Compute the macro recall score."""
        if self.metrics:
            return sum([metric.recall for metric in self.metrics.values()]) / len(self.metrics)
        else:
            return 0

    def pseudo_macro_f1(self) -> float:
        """Compute a "pseudo" macro F1 score by using the values of the macro precision and macro recall.

        TODO: we probably should not use this metric, and use the proper macro F1 score instead.
        """
        if self.metrics and self.macro_precision() + self.macro_recall() > 0:
            return 2 * self.macro_precision() * self.macro_recall() / (self.macro_precision() + self.macro_recall())
        else:
            return 0

    def to_dataframe(self, name: str, fn: Callable[[Metrics], float]) -> pd.DataFrame:
        """Convert the metrics to a DataFrame."""
        series = pd.Series({filename: fn(metric) for filename, metric in self.metrics.items()})
        return series.to_frame(name=name)

    def get_metrics_list(self) -> list[Metrics]:
        """Return a list of all metrics."""
        return list(self.metrics.values())


class DatasetMetricsCatalog:
    """Keeps track of all different relevant metrics that are computed for a dataset."""

    def __init__(self):
        self.metrics: dict[str, DatasetMetrics] = {}

    def document_level_metrics_df(self) -> pd.DataFrame:
        """Return a DataFrame with all the document level metrics."""
        all_series = [
            self.metrics["layer"].to_dataframe("F1", lambda metric: metric.f1),
            self.metrics["layer"].to_dataframe("precision", lambda metric: metric.precision),
            self.metrics["layer"].to_dataframe("recall", lambda metric: metric.recall),
            self.metrics["depth_interval"].to_dataframe("Depth_interval_accuracy", lambda metric: metric.precision),
            self.metrics["layer"].to_dataframe("Number Elements", lambda metric: metric.tp + metric.fn),
            self.metrics["layer"].to_dataframe("Number wrong elements", lambda metric: metric.fp + metric.fn),
            self.metrics["groundwater"].to_dataframe("groundwater", lambda metric: metric.f1),
            self.metrics["groundwater_depth"].to_dataframe("groundwater_depth", lambda metric: metric.f1),
        ]
        document_level_metrics = pd.DataFrame()
        for series in all_series:
            document_level_metrics = document_level_metrics.join(series, how="outer")
        return document_level_metrics

    def metrics_dict(self) -> dict[str, float]:
        """Return a dictionary with the overall metrics."""
        # Initialize a defaultdict to automatically return 0.0 for missing keys
        result = defaultdict(lambda: None)

        # Safely compute groundwater metrics using .get() to avoid KeyErrors
        groundwater_metrics = Metrics.micro_average(
            self.metrics.get("groundwater", DatasetMetrics()).get_metrics_list()
        )
        groundwater_depth_metrics = Metrics.micro_average(
            self.metrics.get("groundwater_depth", DatasetMetrics()).get_metrics_list()
        )

        # Populate the basic metrics
        result.update(
            {
                "F1": self.metrics.get("layer", DatasetMetrics()).pseudo_macro_f1(),
                "recall": self.metrics.get("layer", DatasetMetrics()).macro_recall(),
                "precision": self.metrics.get("layer", DatasetMetrics()).macro_precision(),
                "depth_interval_accuracy": self.metrics.get("depth_interval", DatasetMetrics()).macro_precision(),
                "groundwater_f1": groundwater_metrics.f1,
                "groundwater_recall": groundwater_metrics.recall,
                "groundwater_precision": groundwater_metrics.precision,
                "groundwater_depth_f1": groundwater_depth_metrics.f1,
                "groundwater_depth_recall": groundwater_depth_metrics.recall,
                "groundwater_depth_precision": groundwater_depth_metrics.precision,
            }
        )

        # Add dynamic language-specific metrics only if they exist
        for lang in ["de", "fr"]:
            layer_key = f"{lang}_layer"
            depth_key = f"{lang}_depth_interval"

            if layer_key in self.metrics:
                result[f"{lang}_F1"] = self.metrics[layer_key].pseudo_macro_f1()
                result[f"{lang}_recall"] = self.metrics[layer_key].macro_recall()
                result[f"{lang}_precision"] = self.metrics[layer_key].macro_precision()

            if depth_key in self.metrics:
                result[f"{lang}_depth_interval_accuracy"] = self.metrics[depth_key].macro_precision()

        return dict(result)  # Convert defaultdict back to a regular dict
