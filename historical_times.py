# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Cyber Alpaca
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import statistics
from pathlib import Path
from typing import Dict, List


class HistoricalTimes:
    def __init__(self, file_path: str = "execution_history.json") -> None:
        self.file_path = file_path
        self.execution_history: Dict[str, List[float]] = {}
        self.load_execution_history()

    def load_execution_history(self) -> None:
        """Load historical execution times from a JSON file."""
        if Path(self.file_path).exists():
            with open(self.file_path, "r") as file:
                self.execution_history = json.load(file)

    def save_execution_history(self) -> None:
        """Save historical execution times to a JSON file."""
        with open(self.file_path, "w") as file:
            json.dump(self.execution_history, file, indent=4)

    def update_historical_time(
        self, test_case_name: str, execution_time: float
    ) -> None:
        """Update the historical execution time for a test case."""
        if test_case_name in self.execution_history:
            self.execution_history[test_case_name].append(execution_time)
        else:
            self.execution_history[test_case_name] = [execution_time]

    def get_execution_times(self, test_case_name: str) -> List[float]:
        """Get all historical execution times for a test case."""
        return self.execution_history.get(test_case_name, [])

    def get_average_execution_time(self, test_case_name: str) -> float:
        """Calculate the average execution time for a test case."""
        times = self.get_execution_times(test_case_name)
        return statistics.mean(times) if times else 0.0

    def get_median_execution_time(self, test_case_name: str) -> float:
        """Calculate the median execution time for a test case."""
        times = self.get_execution_times(test_case_name)
        return statistics.median(times) if times else 0.0

    def get_standard_deviation(self, test_case_name: str) -> float:
        """Calculate the standard deviation of execution times for a test case."""
        times = self.get_execution_times(test_case_name)
        return statistics.stdev(times) if len(times) > 1 else 0.0

    def get_all_test_cases(self) -> List[str]:
        """Get a list of all test cases with historical data."""
        return list(self.execution_history.keys())
