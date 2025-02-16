# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Cyber Alpaca
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
from pathlib import Path


class HistoricalTimes:
    def __init__(self, file_path: str = "historical_times.json"):
        self.file_path = file_path
        self.historical_times = {}
        self.load_historical_times()

    def load_historical_times(self) -> None:
        """Load historical execution times from a JSON file and set self.historical_times."""
        if Path(self.file_path).exists():
            with open(self.file_path, "r") as file:
                self.historical_times = json.load(file)

    def save_historical_times(self):
        """Save historical execution times to a JSON file."""
        with open(self.file_path, "w") as file:
            json.dump(self.historical_times, file, indent=4)

    def update_historical_time(
        self,
        test_case_name: str,
        execution_time: float,
        alpha: float = 0.3,
    ):
        """
        Update the historical execution time for a test case using an exponential moving average.

        :param test_case_name: Name of the test case.
        :param execution_time: New execution time.
        :param alpha: Smoothing factor (0 < alpha < 1). Higher alpha gives more weight to recent executions.
        """
        if test_case_name in self.historical_times:
            self.historical_times[test_case_name] = (
                alpha * execution_time
                + (1 - alpha) * self.historical_times[test_case_name]
            )
        else:
            self.historical_times[test_case_name] = execution_time

    def get_average_execution_time(self) -> float:
        """Calculate the average execution time of all test cases."""
        if not self.historical_times:
            return 0.0  # Default fallback if no historical data exists
        return sum(self.historical_times.values()) / len(self.historical_times)

    def get_execution_time(self, test_case_name: str) -> float:
        """
        Get the historical execution time for a test case. If no data exists, return the average execution time.
        """
        return self.historical_times.get(
            test_case_name, self.get_average_execution_time()
        )
