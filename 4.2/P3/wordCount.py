"""
wordCount.py

Counts distinct words (tokens) and their frequencies from a text file.

Usage:
    python wordCount.py fileWithData.txt

Outputs:
    - Prints results to console
    - Writes results to WordCountResults.txt
"""

import sys
import time


RESULTS_FILENAME = "WordCountResults.txt"


def is_printable_token(token: str) -> bool:
    """Return True if all characters in token are printable."""
    index = 0
    length = len(token)
    while index < length:
        char = token[index]
        if not char.isprintable():
            return False
        index += 1
    return True


def tokenize_line(line: str) -> list[str]:
    """
    Tokenize a line into whitespace-separated tokens using basic iteration.
    """
    tokens: list[str] = []
    current_chars: list[str] = []

    i = 0
    line_length = len(line)

    while i < line_length:
        ch = line[i]

        if ch.isspace():
            if len(current_chars) > 0:
                tokens.append("".join(current_chars))
                current_chars = []
        else:
            current_chars.append(ch)

        i += 1

    if len(current_chars) > 0:
        tokens.append("".join(current_chars))

    return tokens


def add_or_increment(counts: dict[str, int], word: str) -> None:
    """
    Increment word count using basic dictionary operations.
    """
    if word in counts:
        counts[word] = counts[word] + 1
    else:
        counts[word] = 1


def sort_items_by_word(items: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """
    Sort (word, count) pairs by word using a basic algorithm (insertion sort).
    """
    sorted_items: list[tuple[str, int]] = []

    i = 0
    while i < len(items):
        item = items[i]
        j = 0

        while j < len(sorted_items):
            if item[1] > sorted_items[j][1]:
                break
            j += 1

        sorted_items.insert(j, item)
        i += 1

    return sorted_items


def format_results(
    filename: str,
    counts: dict[str, int],
    invalid_count: int,
    elapsed_seconds: float,
) -> str:
    """Build the output text for console and file."""
    items: list[tuple[str, int]] = []
    for key in counts:
        items.append((key, counts[key]))

    items = sort_items_by_word(items)

    lines: list[str] = []
    lines.append("Word Count Results")
    lines.append("------------------")
    lines.append(f"Input file: {filename}")
    lines.append(f"Distinct words: {len(counts)}")
    lines.append(f"Invalid tokens: {invalid_count}")
    lines.append("")

    lines.append("Word -> Frequency")
    lines.append("")

    i = 0
    while i < len(items):
        word, freq = items[i]
        lines.append(f"{word} -> {freq}")
        i += 1

    lines.append("")
    lines.append(f"Elapsed time (seconds): {elapsed_seconds:.6f}")

    return "\n".join(lines)


def main() -> int:
    """
    Program entry point.

    This function manages the complete execution of the word count process:
    - Validates command-line arguments.
    - Reads the input text file line by line.
    - Tokenizes each line using whitespace-based parsing.
    - Filters out empty and non-printable tokens.
    - Counts the frequency of each distinct valid token.
    - Measures total execution time.
    - Prints formatted results to standard output.
    - Writes the same results to an output file.

    The program expects exactly one command-line argument:
        python wordCount.py <fileWithData.txt>

    Return codes:
        0  Successful execution.
        1  Input/output error or invalid usage.
    """
    if len(sys.argv) < 2:
        print("Usage: python wordCount.py fileWithData.txt")
        return 1

    input_filename = sys.argv[1]

    start_time = time.perf_counter()

    counts: dict[str, int] = {}
    invalid_tokens = 0

    try:
        with open(input_filename, "r", encoding="utf-8") as file_handle:
            line_number = 0
            for line in file_handle:
                line_number += 1

                tokens = tokenize_line(line)

                t = 0
                while t < len(tokens):
                    token = tokens[t]

                    if len(token) == 0:
                        invalid_tokens += 1
                        print(
                            f"Error: empty token at line {line_number}. "
                            "Skipping and continuing."
                        )
                        t += 1
                        continue

                    if not is_printable_token(token):
                        invalid_tokens += 1
                        print(
                            f"Error: invalid token at line {line_number}: {repr(token)}. "
                            "Skipping and continuing."
                        )
                        t += 1
                        continue

                    add_or_increment(counts, token)
                    t += 1

    except FileNotFoundError:
        print(f"Error: file not found: {input_filename}")
        return 1
    except PermissionError:
        print(f"Error: permission denied: {input_filename}")
        return 1
    except OSError as exc:
        print(f"Error: could not read file: {input_filename}. Details: {exc}")
        return 1

    elapsed = time.perf_counter() - start_time

    output_text = format_results(
        filename=input_filename,
        counts=counts,
        invalid_count=invalid_tokens,
        elapsed_seconds=elapsed,
    )

    print(output_text)

    try:
        with open(RESULTS_FILENAME, "w", encoding="utf-8") as out_handle:
            out_handle.write(output_text)
            out_handle.write("\n")
    except OSError as exc:
        print(f"Error: could not write results file. Details: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
