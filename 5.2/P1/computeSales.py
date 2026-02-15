"""
computeSales.py

Usage:
    python computeSales.py priceCatalogue.json salesRecord.json

Reads a product price catalogue (JSON) and a sales record (JSON), computes totals,
prints a report to stdout and writes it to SalesResults.txt.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


RESULTS_FILE = "SalesResults.txt"


@dataclass(frozen=True)
class SaleLine:
    """Normalized representation of a single sale line item."""
    sale_id: str
    sale_date: str
    product: str
    quantity: float


def eprint(message: str) -> None:
    """Print to stderr."""
    print(message, file=sys.stderr)


def load_json(path: Path) -> Optional[Any]:
    """Load JSON from disk, returning None on error (and reporting it)."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        eprint(f"ERROR: File not found: {path}")
    except PermissionError:
        eprint(f"ERROR: Permission denied reading file: {path}")
    except json.JSONDecodeError as exc:
        eprint(f"ERROR: Invalid JSON in {path}: {exc}")
    except OSError as exc:
        eprint(f"ERROR: Could not read {path}: {exc}")
    return None


def build_price_map(catalogue_json: Any) -> Dict[str, float]:
    """
    Build a mapping: product title -> price.

    Expected catalogue format: list of objects with at least:
        - "title": str
        - "price": number
    """
    prices: Dict[str, float] = {}

    if not isinstance(catalogue_json, list):
        eprint("ERROR: Catalogue JSON must be a list of products.")
        return prices

    for idx, item in enumerate(catalogue_json):
        if not isinstance(item, dict):
            eprint(f"ERROR: Catalogue item #{idx} is not an object; skipping.")
            continue

        title = item.get("title")
        price = item.get("price")

        if not isinstance(title, str) or not title.strip():
            eprint(f"ERROR: Catalogue item #{idx} missing/invalid 'title'; skipping.")
            continue

        if not isinstance(price, (int, float)):
            eprint(
                f"ERROR: Catalogue item '{title}' has invalid 'price'={price!r}; "
                "skipping."
            )
            continue

        if price < 0:
            eprint(
                f"ERROR: Catalogue item '{title}' has negative price={price}; skipping."
            )
            continue

        # If duplicates exist, last one wins (but warn).
        if title in prices:
            eprint(
                f"WARNING: Duplicate catalogue title '{title}'. "
                "Overwriting previous price."
            )

        prices[title] = float(price)

    return prices


def iter_sales_lines(sales_json: Any) -> Iterable[Tuple[int, Any]]:
    """
    Yield (index, sale_item) from the sales JSON.

    Expected sales format: list of objects (each object is a line item).
    """
    if not isinstance(sales_json, list):
        eprint("ERROR: Sales JSON must be a list of sale line items.")
        return []

    return enumerate(sales_json)


def parse_sale_line(idx: int, raw: Any) -> Optional[SaleLine]:
    """
    Parse and validate a sale line item.

    Expected keys (case-sensitive as per examples):
        - "SALE_ID"
        - "SALE_Date"
        - "Product"
        - "Quantity"
    """
    if not isinstance(raw, dict):
        eprint(f"ERROR: Sales item #{idx} is not an object; skipping.")
        return None

    sale_id = raw.get("SALE_ID")
    sale_date = raw.get("SALE_Date")
    product = raw.get("Product")
    quantity = raw.get("Quantity")

    if sale_id is None:
        eprint(f"ERROR: Sales item #{idx} missing 'SALE_ID'; skipping.")
        return None

    if not isinstance(sale_date, str) or not sale_date.strip():
        eprint(f"ERROR: Sales item #{idx} missing/invalid 'SALE_Date'; skipping.")
        return None

    if not isinstance(product, str) or not product.strip():
        eprint(f"ERROR: Sales item #{idx} missing/invalid 'Product'; skipping.")
        return None

    if not isinstance(quantity, (int, float)):
        eprint(
            f"ERROR: Sales item #{idx} has invalid 'Quantity'={quantity!r}; skipping."
        )
        return None

    qty = float(quantity)
    if qty <= 0:
        eprint(
            f"ERROR: Sales item #{idx} has non-positive Quantity={qty}; skipping."
        )
        return None

    return SaleLine(
        sale_id=str(sale_id),
        sale_date=sale_date.strip(),
        product=product.strip(),
        quantity=qty,
    )


def money(value: float) -> str:
    """Format a float as currency-like with 2 decimals."""
    return f"{value:,.2f}"


def compute_totals(
    prices: Dict[str, float],
    sales_json: Any,
) -> Tuple[
    float,
    Dict[str, float],
    Dict[str, int],
    List[str],
]:
    """
    Compute totals.

    Returns:
        grand_total
        totals_by_sale_id
        lines_count_by_sale_id
        warnings (human-readable)
    """
    grand_total = 0.0
    totals_by_sale_id: Dict[str, float] = {}
    lines_count_by_sale_id: Dict[str, int] = {}
    warnings: List[str] = []

    for idx, raw in iter_sales_lines(sales_json):
        sale_line = parse_sale_line(idx, raw)
        if sale_line is None:
            continue

        unit_price = prices.get(sale_line.product)
        if unit_price is None:
            msg = (
                f"WARNING: Unknown product '{sale_line.product}' "
                f"(sale_id={sale_line.sale_id}, item #{idx}); skipping line."
            )
            eprint(msg)
            warnings.append(msg)
            continue

        line_total = unit_price * sale_line.quantity
        grand_total += line_total

        totals_by_sale_id[sale_line.sale_id] = (
            totals_by_sale_id.get(sale_line.sale_id, 0.0) + line_total
        )
        lines_count_by_sale_id[sale_line.sale_id] = (
            lines_count_by_sale_id.get(sale_line.sale_id, 0) + 1
        )

    return grand_total, totals_by_sale_id, lines_count_by_sale_id, warnings


def render_report(
    catalogue_path: Path,
    sales_path: Path,
    grand_total: float,
    totals_by_sale_id: Dict[str, float],
    lines_count_by_sale_id: Dict[str, int],
    elapsed_seconds: float,
) -> str:
    """Create a human-readable report."""
    sale_ids_sorted = sorted(
        totals_by_sale_id.keys(),
        key=lambda x: (int(x) if x.isdigit() else x),
    )

    lines: List[str] = []
    lines.append("SALES RESULTS")
    lines.append("=" * 60)
    lines.append(f"Catalogue file : {catalogue_path}")
    lines.append(f"Sales file     : {sales_path}")
    lines.append("-" * 60)
    lines.append("Totals by SALE_ID")
    lines.append("-" * 60)

    if not sale_ids_sorted:
        lines.append("No valid sales lines were processed.")
    else:
        header = f"{'SALE_ID':<12}{'LINES':>8}{'TOTAL':>20}"
        lines.append(header)
        lines.append(f"{'-' * 12}{'-' * 8}{'-' * 20}")
        for sale_id in sale_ids_sorted:
            count = lines_count_by_sale_id.get(sale_id, 0)
            total = totals_by_sale_id.get(sale_id, 0.0)
            lines.append(f"{sale_id:<12}{count:>8}{money(total):>20}")

    lines.append("-" * 60)
    lines.append(f"GRAND TOTAL: {money(grand_total)}")
    lines.append(f"Elapsed time: {elapsed_seconds:.6f} seconds")
    lines.append("=" * 60)
    lines.append("")

    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    """Write text to disk, reporting errors but not crashing."""
    try:
        with path.open("w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        eprint(f"ERROR: Could not write results file {path}: {exc}")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Compute total sales cost from a price catalogue and sales record."
    )
    parser.add_argument(
        "catalogue",
        type=Path,
        help="Path to priceCatalogue.json",
    )
    parser.add_argument(
        "sales",
        type=Path,
        help="Path to salesRecord.json",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Program entry point."""
    args = parse_args(argv)

    start = time.perf_counter()

    catalogue_json = load_json(args.catalogue)
    sales_json = load_json(args.sales)

    if catalogue_json is None or sales_json is None:
        eprint("ERROR: Cannot continue due to previous errors.")
        return 2

    prices = build_price_map(catalogue_json)

    if not prices:
        eprint("ERROR: No valid products/prices loaded from catalogue.")
        # Continue anyway; will just skip all unknown products.

    grand_total, totals_by_sale_id, lines_count_by_sale_id, _warnings = compute_totals(
        prices=prices,
        sales_json=sales_json,
    )

    elapsed = time.perf_counter() - start

    report = render_report(
        catalogue_path=args.catalogue,
        sales_path=args.sales,
        grand_total=grand_total,
        totals_by_sale_id=totals_by_sale_id,
        lines_count_by_sale_id=lines_count_by_sale_id,
        elapsed_seconds=elapsed,
    )

    print(report, end="")
    write_text(Path(RESULTS_FILE), report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
