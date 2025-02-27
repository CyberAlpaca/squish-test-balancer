# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Cyber Alpaca
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import Dict, List, Tuple

import yaml

from historical_times import HistoricalTimes
from logger import logger

history = HistoricalTimes()


@dataclass
class SquishServer:
    host: str
    port: int

    def __str__(self):
        return f"{self.host}:{self.port}"


class TestCase:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.suite = path.parent

    def __str__(self):
        return f"TestCase(name={self.name}, suite={self.suite})"


class Config:
    _instance = None

    def __new__(cls, config_file=None):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            if config_file:
                cls._instance.load_config(config_file)
        return cls._instance

    def load_config(self, config_file: str):
        try:
            with open(config_file, "r") as file:
                logger.debug(f"Loading config file: {config_file}")
                self.config = yaml.safe_load(file)
                # Load Squish servers
                self._squish_servers = []
                for server in self.config.get("squish_servers", []):
                    logger.debug(f"Found server: {server}")
                    host, port = server.split(":")
                    self._squish_servers.append(SquishServer(host, int(port)))

                # Load squishrunner path
                self._squishrunner_path = self.config.get("squishrunner_path")
                logger.debug(f"Using squishrunner: {self.squishrunner_path}")

                # Load test suites directory
                self._test_suites_dir = self.config.get("test_suites_dir")
                logger.debug(f"Test suites directory: {self.test_suites_dir}")

        except Exception as e:
            logger.error(f"Error loading config file {config_file}: {e}")
            sys.exit(1)

    @property
    def squishservers(self) -> List[SquishServer]:
        return self._squish_servers

    @property
    def squishrunner_path(self) -> str:
        return self._squishrunner_path

    @property
    def test_suites_dir(self) -> str:
        return self._test_suites_dir


def run_squish_test(
    test_case: TestCase, squish_server: SquishServer
) -> Tuple[str, bool, float]:
    try:
        start_time = time.time()
        command = (
            f"{Config().squishrunner_path} --host {squish_server.host} --port {squish_server.port} "
            f"--testsuite {test_case.suite} --testcase {test_case.name} "
            "--exitCodeOnFail 44 --reportgen null"
        )
        logger.info(f"Execute {test_case}")
        logger.debug(f"Running command: {command}")
        subprocess.run(command, shell=True, check=True)
        end_time = time.time()
        execution_time = end_time - start_time

        history.update_historical_time(test_case.name, execution_time)

        return (str(test_case), True, execution_time)

    except subprocess.CalledProcessError as e:
        end_time = time.time()
        execution_time = end_time - start_time

        history.update_historical_time(test_case.name, execution_time)

        if e.returncode == 44:
            logger.debug(f"Test case {test_case} failed on server {squish_server}: {e}")
            return (str(test_case), False, execution_time)
        else:
            logger.error(
                f"Test case {test_case} encountered an unexpected error on server {squish_server}: \n{e}"
            )
            return (str(test_case), False, execution_time)


def distribute_tests(
    test_cases: List[TestCase],
    squish_servers: List[SquishServer],
) -> Dict[TestCase, Tuple[bool, str, float]]:
    results = {}
    test_case_queue = Queue()
    server_test_counts = {str(server): 0 for server in squish_servers}

    for test_case in test_cases:
        test_case_queue.put(test_case)

    def worker(server: SquishServer):
        while not test_case_queue.empty():
            try:
                test_case = test_case_queue.get_nowait()
                result = run_squish_test(test_case, server)
                results[test_case] = [result[1], str(server), result[2]]
                server_test_counts[str(server)] += 1
                test_case_queue.task_done()
            except Exception as e:
                logger.error(
                    f"Error processing test case {test_case} on server {server}: {e}"
                )
                test_case_queue.task_done()

    with ThreadPoolExecutor(max_workers=len(squish_servers)) as executor:
        futures = [executor.submit(worker, server) for server in squish_servers]
        for future in futures:
            future.result()

    for server, count in server_test_counts.items():
        logger.info(f"Server {server} executed {count} test cases")

    return results


def find_test_cases(test_suites_dir: str) -> List[TestCase]:
    logger.debug(f"Finding test cases in {test_suites_dir}")
    test_cases = []
    test_cases_path = Path(test_suites_dir)

    for test_case_path in test_cases_path.rglob("tst_*"):
        if test_case_path.is_dir():
            logger.debug(f"Found test case: {test_case_path}")
            test_cases.append(TestCase(test_case_path))
    logger.info(f"Found {len(test_cases)} test cases")
    return test_cases


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the script.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run Squish test cases distributed across multiple squishservers.",
        epilog="Example usage: python main.py /path/to/test_suites /path/to/config.yaml",
    )

    parser.add_argument(
        "test_suites_dir",
        type=str,
        nargs="?",
        default=None,
        help="Directory containing the Squish test suites",
    )

    parser.add_argument(
        "config_file",
        type=str,
        help="Path to the config file.",
    )

    # Add an optional argument for verbosity
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase output verbosity",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Load config to get the default test_suites_dir
    config = Config(args.config_file)

    # If test_suites_dir is not provided via command line, use the one from config
    if args.test_suites_dir is None:
        if config.test_suites_dir is None:
            logger.error(
                "No test suites directory provided via command line or config file."
            )
            sys.exit(1)
        args.test_suites_dir = config.test_suites_dir

    # Validate the test_suites_dir
    if not Path(args.test_suites_dir).is_dir():
        parser.error(
            f"The specified test_suites_dir '{args.test_suites_dir}' does not exist or is not a directory."
        )

    # Validate the config_file
    if not Path(args.config_file).is_file():
        parser.error(
            f"The specified config_file '{args.config_file}' does not exist or is not a file."
        )

    return args


def sort_test_cases_by_execution_time(test_cases: List[TestCase]) -> List[TestCase]:
    """
    Sort test cases by their historical execution time (longest first).

    :param test_cases: List of TestCase objects to sort.
    :return: List of TestCase objects sorted by execution time (longest first).
    """
    return sorted(
        test_cases,
        key=lambda tc: history.get_average_execution_time(tc.name),
        reverse=True,  # Sort in descending order (longest first)
    )


def main():
    args = parse_args()
    if args.verbose:
        logger.setLevel(logger.logging.DEBUG)

    config = Config(args.config_file)
    squish_servers = config.squishservers

    if not squish_servers:
        logger.error("No squishservers found in the provided YAML file.")
        sys.exit(1)

    test_cases = find_test_cases(args.test_suites_dir)
    if not test_cases:
        logger.error("No test cases found in the provided directory.")
        sys.exit(1)
    # Sort test cases by execution time (longest first)
    sorted_test_cases = sort_test_cases_by_execution_time(test_cases)

    # Print sorted test cases
    for test_case in sorted_test_cases:
        avg_time = history.get_average_execution_time(test_case.name)
        logger.info(
            f"Test Case: {test_case.name}, " f"Average Execution Time: {avg_time:.2f}s"
        )
    results = distribute_tests(test_cases, squish_servers)
    history.save_execution_history()

    logger.info("Test execution results:")
    for test_case, result in results.items():
        if result[0]:
            logger.info(
                f"\x1b[32;20mPASS\x1b[0m {result[1]} {test_case} ({result[2]:.2f}s)"
            )
        else:
            logger.info(
                f"\x1b[31;20mFAIL\x1b[0m {result[1]} {test_case} ({result[2]:.2f}s)"
            )


if __name__ == "__main__":
    logger.info("Starting balancer...")
    main()
