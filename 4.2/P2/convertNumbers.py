"""
convertNumbers.py

Reads a file containing items (presumably numbers), converts valid integers
to binary and hexadecimal using basic algorithms (no bin/hex/format),
prints results to screen, and writes them to ConvertionResults.txt.

Usage:
    python convertNumbers.py fileWithData.txt
"""

import sys
import time
from typing import Optional, Tuple


RESULTS_FILENAME = "ConvertionResults.txt"
HEX_DIGITS = "0123456789ABCDEF"


def parse_int(text: str) -> Optional[int]:
    """
    Parse a string into an integer.

    Supports optional leading + or - and decimal digits only.
    Returns None if invalid.
    """
    s = text.strip()
    if not s:
        return None

    sign = 1
    idx = 0

    if s[0] == "+":
        idx = 1
    elif s[0] == "-":
        sign = -1
        idx = 1

    if idx >= len(s):
        return None

    value = 0
    for ch in s[idx:]:
        if ch < "0" or ch > "9":
            return None
        digit = ord(ch) - ord("0")
        value = value * 10 + digit

    return sign * value


def to_base(n: int, base: int) -> str:
    """
    Convert integer n to a string in the given base using manual division.
    """
    if base < 2 or base > 16:
        raise ValueError("Base must be between 2 and 16.")

    if n == 0:
        return "0"

    sign = ""
    if n < 0:
        sign = "-"
        n = -n

    digits = []
    while n > 0:
        remainder = n % base
        digits.append(HEX_DIGITS[remainder])
        n //= base

    digits.reverse()
    return sign + "".join(digits)


def convert_number(n: int) -> Tuple[str, str]:
    """Return (binary_str, hex_str) for integer n."""
    binary_str = to_base(n, 2)
    hex_str = to_base(n, 16)
    return binary_str, hex_str


def format_result_line(original: str, binary_str: str, hex_str: str) -> str:
    """Format one output line for a valid conversion."""
    return f"{original}\tBIN={binary_str}\tHEX={hex_str}"


def format_error_line(line_no: int, raw: str) -> str:
    """Format an error message for invalid input."""
    cleaned = raw.rstrip("\n")
    return f"ERROR line {line_no}: invalid integer -> {cleaned!r}"


def main() -> int:
    """
    Program entry point.

    This function controls the full execution flow of the script:
    - Validates command-line arguments.
    - Reads the input text file line by line.
    - Parses each line as a signed decimal integer using a manual parser.
    - Converts valid integers to binary and hexadecimal representations 
     using base-conversion algorithms (no built-in helpers).
    - Collects and reports invalid input lines.
    - Measures total execution time.
    - Prints results to standard output and errors to standard error.
    - Writes all results and errors to an output file.

    The program expects exactly one command-line argument:
        python convertNumbers.py <fileWithData.txt>

    Return codes:
        0  Success.
        1  File I/O error (input or output).
        2  Invalid or missing command-line arguments.
    """
    if len(sys.argv) < 2:
        print("Usage: python convertNumbers.py fileWithData.txt")
        return 2

    input_filename = sys.argv[1]

    start_time = time.perf_counter()

    output_lines = []
    error_lines = []

    try:
        with open(input_filename, "r", encoding="utf-8") as infile:
            for line_no, raw_line in enumerate(infile, start=1):
                stripped = raw_line.strip()

                # Treat empty lines as invalid data (can be changed if desired).
                parsed = parse_int(stripped)
                if parsed is None:
                    err = format_error_line(line_no, raw_line)
                    error_lines.append(err)
                    continue

                binary_str, hex_str = convert_number(parsed)
                output_lines.append(
                    format_result_line(stripped, binary_str, hex_str)
                )
    except FileNotFoundError:
        print(f"ERROR: file not found: {input_filename}")
        return 1
    except OSError as exc:
        print(f"ERROR: could not read file {input_filename}: {exc}")
        return 1

    elapsed = time.perf_counter() - start_time
    elapsed_line = f"TIME_ELAPSED_SECONDS={elapsed:.6f}"

    # Print to console
    for line in output_lines:
        print(line)
    for err in error_lines:
        print(err, file=sys.stderr)
    print(elapsed_line)

    # Write to results file
    try:
        with open(RESULTS_FILENAME, "w", encoding="utf-8") as outfile:
            for line in output_lines:
                outfile.write(line + "\n")
            for err in error_lines:
                outfile.write(err + "\n")
            outfile.write(elapsed_line + "\n")
    except OSError as exc:
        print(f"ERROR: could not write {RESULTS_FILENAME}: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
