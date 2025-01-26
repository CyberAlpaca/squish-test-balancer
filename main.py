# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Cyber Alpaca
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import Dict, List, Tuple

import yaml

from my_logger import logger


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
                self.squish_servers = []
                for server in self.config.get("squish_servers", []):
                    logger.debug(f"Found server: {server}")
                    host, port = server.split(":")
                    self.squish_servers.append(SquishServer(host, int(port)))

                # Load squishrunner path
                self.squishrunner_path = self.config.get("squishrunner_path")
                logger.debug(f"Using squishrunner: {self.squishrunner_path}")

        except Exception as e:
            logger.error(f"Error loading config file {config_file}: {e}")
            sys.exit(1)

    def squishservers(self) -> List[SquishServer]:
        return self.squish_servers

    def squishrunner_path(self) -> str:
        return self.squishrunner_path


def run_squish_test(
    test_case: TestCase, squish_server: SquishServer
) -> Tuple[str, bool]:
    try:
        command = (
            f"{Config().squishrunner_path} --host {squish_server.host} --port {squish_server.port} "
            f"--testsuite {test_case.suite} --testcase {test_case.name} "
            "--exitCodeOnFail 44 --reportgen null"
        )
        logger.info(f"Execute {test_case}")
        logger.debug(f"Running command: {command}")
        subprocess.run(command, shell=True, check=True)
        return (str(test_case), True)

    except subprocess.CalledProcessError as e:
        if e.returncode == 44:
            logger.debug(f"Test case {test_case} failed on server {squish_server}: {e}")
            return (str(test_case), False)
        else:
            logger.error(
                f"Test case {test_case} encountered an unexpected error on server {squish_server}: \n{e}"
            )
            return (str(test_case), False)


def distribute_tests(
    test_cases: List[TestCase], squish_servers: List[SquishServer]
) -> Dict[TestCase, bool]:
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
                results[test_case] = [result[1], str(server)]
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


def find_test_cases(test_cases_dir: str) -> List[TestCase]:
    logger.debug(f"Finding test cases in {test_cases_dir}")
    test_cases = []
    test_cases_path = Path(test_cases_dir)

    for test_case_path in test_cases_path.rglob("tst_*"):
        if test_case_path.is_dir():
            logger.debug(f"Found test case: {test_case_path}")
            test_cases.append(TestCase(test_case_path))
    logger.info(f"Found {len(test_cases)} test cases")
    return test_cases


def main():
    parser = argparse.ArgumentParser(
        description="Run Squish test cases distributed across multiple squishservers.",
        epilog="Example usage: python main.py /path/to/test_cases /path/to/config.yaml",
    )

    parser.add_argument(
        "test_cases_dir",
        type=str,
        help="Directory containing the Squish test cases (directories starting with tst_)",
    )

    parser.add_argument(
        "config_file",
        type=str,
        help="Path to the config file. Example YAML structure:\n"
        "squish_servers:\n"
        "  - 192.168.1.100:4432\n"
        "  - 192.168.1.100:4433\n"
        "squishrunner_path: D:/Squish/bin/squishrunner\n",
    )

    args = parser.parse_args()

    test_cases_dir = args.test_cases_dir

    config = Config(args.config_file)
    squish_servers = config.squishservers()

    if not squish_servers:
        logger.error("No squishservers found in the provided YAML file.")
        sys.exit(1)

    test_cases = find_test_cases(test_cases_dir)
    if not test_cases:
        logger.error("No test cases found in the provided directory.")
        sys.exit(1)

    results = distribute_tests(test_cases, squish_servers)

    logger.info("Test execution results:")
    for test_case, result in results.items():
        if result[0]:
            logger.info(f"\x1b[32;20mPASS\x1b[0m {result[1]} {test_case}")
        else:
            logger.info(f"\x1b[31;20mFAIL\x1b[0m {result[1]} {test_case}")


if __name__ == "__main__":
    logger.info("Starting balancer...")
    main()
