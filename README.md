# Squish Test Distributor

The **Squish Test Distributor** is a Python-based tool designed to distribute and execute Squish test cases across multiple Squish servers efficiently. It leverages historical execution times to optimize the distribution of test cases, ensuring that longer-running tests are prioritized and balanced across available servers. This tool is particularly useful for teams running large test suites and looking to reduce overall execution time.

## Features

- **Distributed Execution**: Run Squish test cases across multiple Squish servers in parallel.
- **Historical Execution Tracking**: Track and utilize historical execution times to optimize test distribution.
- **Dynamic Load Balancing**: Automatically balance the load across servers based on test case execution times.
- **Detailed Logging**: Color-coded logging for easy monitoring of test execution and results.
- **Configurable**: Easily configure Squish servers, test directories, and other parameters via a YAML configuration file.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/CyberAlpaca/squish-test-distributor.git
   cd squish-test-distributor
   ```

2. **Python Installation**:
   Ensure you have Python 3.7+ installed.

3. **Configure**:
   Edit the `config.yaml` file to specify your squishservers, squishrunner path, and test suites directory.

   Example `config.yaml`:
   ```yaml
   squish_servers:
     - 192.168.1.100:4432
     - 192.168.1.101:4432
   squishrunner_path: /path/to/squishrunner
   test_suites_dir: /path/to/test_cases
   ```

## Usage

Run the distributor with the following command:

```bash
python main.py /path/to/config.yaml
```

### Command-Line Arguments

- `test_suites_dir`: [Optional] Directory containing the Squish test cases (directories starting with `tst_`).
- `config_file`: Path to the configuration file (YAML format).
- `-v, --verbose`: Increase output verbosity.

### Example

```bash
python main.py /path/to/config.yaml --verbose
```

## Historical Execution Times

The tool tracks the execution times of test cases and uses this data to optimize future test distributions. Historical data is stored in a JSON file (`execution_history.json`) and can be used to calculate average, median, and standard deviation of execution times.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the BSD 3-Clause License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Squish**: The GUI test automation tool by [Qt](https://qt.io).

## Support

For any issues or questions, please open an issue on the [GitHub repository](https://github.com/CyberAlpaca/squish-test-distributor/issues).

---

**Happy Testing!** 🚀
