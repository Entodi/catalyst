from typing import Any, Dict, List

import torch

from catalyst.metrics._additive import AdditiveValueMetric
from catalyst.metrics._metric import ICallbackBatchMetric
from catalyst.metrics.functional._hitrate import hitrate


class HitrateMetric(ICallbackBatchMetric):
    """Calculates the hitrate.

    Args:
        topk_args: list of `topk` for hitrate@topk computing
        compute_on_call: if True, computes and returns metric value during metric call
        prefix: metric prefix
        suffix: metric suffix

    Compute mean value of hitrate and it's approximate std value.
    """

    def __init__(
        self,
        topk_args: List[int] = None,
        compute_on_call: bool = True,
        prefix: str = None,
        suffix: str = None,
    ):
        """Init HitrateMetric"""
        super().__init__(compute_on_call=compute_on_call, prefix=prefix, suffix=suffix)
        self.metric_name_mean = f"{self.prefix}hitrate{self.suffix}"
        self.metric_name_std = f"{self.prefix}hitrate{self.suffix}/std"
        self.topk_args: List[int] = topk_args or [1]
        self.additive_metrics: List[AdditiveValueMetric] = [
            AdditiveValueMetric() for _ in range(len(self.topk_args))
        ]

    def reset(self) -> None:
        """Reset all fields"""
        for metric in self.additive_metrics:
            metric.reset()

    def update(self, logits: torch.Tensor, targets: torch.Tensor) -> List[float]:
        """
        Update metric value with hitrate for new data and return intermediate metrics values.

        Args:
            logits (torch.Tensor): tensor of logits
            targets (torch.Tensor): tensor of targets

        Returns:
            list of hitrate@k values
        """
        values = hitrate(logits, targets, topk=self.topk_args)
        values = [v.item() for v in values]
        for value, metric in zip(values, self.additive_metrics):
            metric.update(value, len(targets))
        return values

    def update_key_value(self, logits: torch.Tensor, targets: torch.Tensor) -> Dict[str, float]:
        """
        Update metric value with hitrate for new data and return intermediate metrics
        values in key-value format.

        Args:
            logits (torch.Tensor): tensor of logits
            targets (torch.Tensor): tensor of targets

        Returns:
            dict of hitrate@k values
        """
        values = self.update(logits=logits, targets=targets)
        output = {
            f"{self.prefix}hitrate{key:02d}{self.suffix}": value
            for key, value in zip(self.topk_args, values)
        }
        output[self.metric_name_mean] = output[f"{self.prefix}hitrate01{self.suffix}"]
        return output

    def compute(self) -> Any:
        """
        Compute hitrate for all data

        Returns:
            list of mean values, list of std values
        """
        means, stds = zip(*(metric.compute() for metric in self.additive_metrics))
        return means, stds

    def compute_key_value(self) -> Dict[str, float]:
        """
        Compute hitrate for all data and return results in key-value format

        Returns:
            dict of metrics
        """
        means, stds = self.compute()
        output_mean = {
            f"{self.prefix}hitrate{key:02d}{self.suffix}": value
            for key, value in zip(self.topk_args, means)
        }
        output_std = {
            f"{self.prefix}hitrate{key:02d}{self.suffix}/std": value
            for key, value in zip(self.topk_args, stds)
        }
        output_mean[self.metric_name_mean] = output_mean[f"{self.prefix}hitrate01{self.suffix}"]
        output_std[self.metric_name_std] = output_std[f"{self.prefix}hitrate01{self.suffix}/std"]
        return {**output_mean, **output_std}


__all__ = ["HitrateMetric"]
