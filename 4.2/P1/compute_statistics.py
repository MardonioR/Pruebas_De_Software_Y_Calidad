"""
computeStatistics.py

Usage:
    python computeStatistics.py fileWithData.txt

Reads a text file containing items (presumably numbers), one per line or
separated by whitespace/commas, computes descriptive statistics using
basic algorithms (no statistics libraries), prints results to console,
and writes them to StatisticsResults.txt.

Statistics:
- mean
- median
- mode (can be multiple)
- variance (population)
- standard deviation (population)

Invalid data is reported to stderr and ignored; execution continues.
"""

from __future__ import annotations

import sys
import time
from typing import List, Tuple


RESULTS_FILENAME = "StatisticsResults.txt"


def parse_numbers_from_file(path: str) -> Tuple[List[float], int]:
    """
    Parse numbers from a file.

    Accepts numbers separated by whitespace and/or commas.
    Returns (numbers, invalid_count). Invalid tokens are reported.
    """
    numbers: List[float] = []
    invalid_count = 0

    try:
        with open(path, "r", encoding="utf-8") as file:
            for line_no, line in enumerate(file, start=1):
                # Allow commas as separators too.
                cleaned = line.replace(",", " ")
                tokens = cleaned.split()

                for token in tokens:
                    try:
                        value = float(token)
                        numbers.append(value)
                    except ValueError:
                        invalid_count += 1
                        print(
                            f"Invalid data ignored at line {line_no}: {token!r}",
                            file=sys.stderr,
                        )
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"Error reading file {path}: {exc}", file=sys.stderr)
        sys.exit(1)

    return numbers, invalid_count


def mean(values: List[float]) -> float:
    """
    Compute meanusing put of a list of values.

    Returns a list:
    - single float number corresponding to mean.
    """
    total = 0.0
    count = 0
    for v in values:
        total += v
        count += 1
    return total / count


def sort_values(values: List[float]) -> List[float]:
    """
    Return a sorted copy using a basic O(n log n) algorithm (merge sort).
    """
    if len(values) <= 1:
        return values[:]

    mid = len(values) // 2
    left = sort_values(values[:mid])
    right = sort_values(values[mid:])

    merged: List[float] = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    while i < len(left):
        merged.append(left[i])
        i += 1

    while j < len(right):
        merged.append(right[j])
        j += 1

    return merged


def median(values: List[float]) -> float:
    """
    Compute median.

    Returns a list:
    - single float number corresponding to median.
    """
    ordered = sort_values(values)
    n = len(ordered)
    mid = n // 2

    if n % 2 == 1:
        return ordered[mid]

    return (ordered[mid - 1] + ordered[mid]) / 2.0


def mode(values: List[float]) -> List[float]:
    """
    Compute mode(s) using counting via a dictionary.

    Returns a list:
    - empty list if no mode (all values appear once)
    - one or more values if there are ties for highest frequency
    """
    counts: dict[float, int] = {}
    for v in values:
        if v in counts:
            counts[v] += 1
        else:
            counts[v] = 1

    max_count = 0
    for c in counts.values():
        max_count = max(max_count, c)

    if max_count <= 1:
        return []

    modes: List[float] = []
    for v, c in counts.items():
        if c == max_count:
            modes.append(v)

    # Sort modes for stable output (using our merge sort).
    return sort_values(modes)


def variance(values: List[float], avg: float) -> float:
    """
    Population variance:
        sum((x - mean)^2) / n
    """
    total = 0.0
    count = 0
    for v in values:
        diff = v - avg
        total += diff * diff
        count += 1
    return total / count


def sqrt_newton(value: float) -> float:
    """
    Square root using Newton-Raphson iteration.
    """
    if value < 0.0:
        raise ValueError("Cannot compute square root of a negative number.")
    if value == 0.0:
        return 0.0

    x = value
    for _ in range(50):
        prev = x
        x = 0.5 * (x + value / x)
        if abs(x - prev) < 1e-12:
            break
    return x


def standard_deviation(var: float) -> float:
    """
    Calculates sqrt given the variance parameter.
    """
    return sqrt_newton(var)


def format_results(
    count: int,
    invalid_count: int,
    avg: float,
    med: float,
    modes: List[float],
    var: float,
    std: float,
    elapsed_seconds: float,
) -> str:
    """
    Fromats final results.
    """
    if modes:
        mode_str = ", ".join(str(m) for m in modes)
    else:
        mode_str = "No mode"

    lines = [
        "Descriptive Statistics Results",
        "------------------------------",
        f"Valid items: {count}",
        f"Invalid items ignored: {invalid_count}",
        "",
        f"Mean: {avg}",
        f"Median: {med}",
        f"Mode: {mode_str}",
        f"Variance (population): {var}",
        f"Standard deviation (population): {std}",
        "",
        f"Time elapsed (seconds): {elapsed_seconds}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """
    Entry point of the program.

    This function orchestrates the full execution flow:
    - Validates command-line arguments.
    - Reads and parses numeric data from the input file.
    - Computes descriptive statistics (mean, median, mode, variance,
      and population standard deviation).
    - Measures execution time.
    - Prints the results to standard output.
    - Writes the results to a text file.

    The program expects exactly one command-line argument:
        python computeStatistics.py <fileWithData.txt>

    If the input file cannot be read, contains no valid numeric data,
    or if an output error occurs, the program terminates with a
    non-zero exit code and reports the error to stderr.
    """
    if len(sys.argv) < 2:
        print(
            "Usage: python computeStatistics.py fileWithData.txt",
            file=sys.stderr,
        )
        sys.exit(2)

    input_path = sys.argv[1]

    start = time.perf_counter()

    values, invalid_count = parse_numbers_from_file(input_path)
    if not values:
        print("Error: no valid numeric data found.", file=sys.stderr)
        sys.exit(1)

    avg = mean(values)
    med = median(values)
    modes = mode(values)
    var = variance(values, avg)
    std = standard_deviation(var)

    elapsed = time.perf_counter() - start

    output = format_results(
        count=len(values),
        invalid_count=invalid_count,
        avg=avg,
        med=med,
        modes=modes,
        var=var,
        std=std,
        elapsed_seconds=elapsed,
    )

    print(output, end="")

    try:
        with open(RESULTS_FILENAME, "w", encoding="utf-8") as file:
            file.write(output)
    except OSError as exc:
        print(f"Error writing results file: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
