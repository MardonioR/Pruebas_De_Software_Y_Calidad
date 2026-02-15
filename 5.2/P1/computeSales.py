"""
computeSales.py

Usage:
    python computeSales.py priceCatalogue.json salesRecord.json

Reads:
- priceCatalogue.json: product price catalogue (JSON)
- salesRecord.json: sales records (JSON)

Computes total cost of all sales, prints results to console and writes them to
SalesResults.txt. Handles invalid data gracefully (logs errors and continues).
"""

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union


RESULTS_FILE_NAME = "SalesResults.txt"


@dataclass(frozen=True)
class LineItem:
    """A normalized sale line item."""
    product: str
    quantity: float


def eprint(message: str) -> None:
    """Print to stderr."""
    print(message, file=sys.stderr)


def load_json(path: Union[str, Path]) -> Optional[Any]:
    """Load JSON from a file. Return None on error (and report it)."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        eprint(f"ERROR: File not found: {path}")
    except PermissionError:
        eprint(f"ERROR: Permission denied reading file: {path}")
    except json.JSONDecodeError as exc:
        eprint(f"ERROR: Invalid JSON in file {path}: {exc}")
    except OSError as exc:
        eprint(f"ERROR: Could not read file {path}: {exc}")
    return None


def _as_float(value: Any) -> Optional[float]:
    """Convert value to float if possible; otherwise return None."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN check
        return None
    return number


def parse_catalogue(raw: Any) -> Tuple[Dict[str, float], List[str]]:
    """
    Parse a price catalogue into a dict: {product_name: price}.
    Supports common JSON shapes:
      1) {"ProductA": 10.5, "ProductB": 2}
      2) [{"title": "ProductA", "price": 10.5}, ...]
      3) {"products": [{"name": "...", "price": ...}, ...]}
    """
    errors: List[str] = []
    catalogue: Dict[str, float] = {}

    def add_product(name: Any, price: Any, context: str) -> None:
        if not isinstance(name, str) or not name.strip():
            errors.append(f"Catalogue error ({context}): invalid product name: {name!r}")
            return
        price_num = _as_float(price)
        if price_num is None or price_num < 0:
            errors.append(
                f"Catalogue error ({context}): invalid price for {name!r}: {price!r}"
            )
            return
        catalogue[name.strip()] = price_num

    if isinstance(raw, dict):
        if "products" in raw and isinstance(raw["products"], list):
            for idx, item in enumerate(raw["products"]):
                if not isinstance(item, dict):
                    errors.append(
                        f"Catalogue error (products[{idx}]): expected object, got {type(item).__name__}"
                    )
                    continue
                name = item.get("name", item.get("title", item.get("product")))
                price = item.get("price", item.get("cost"))
                add_product(name, price, f"products[{idx}]")
        else:
            # Assume mapping of product -> price
            for key, value in raw.items():
                add_product(key, value, f"mapping[{key!r}]")
    elif isinstance(raw, list):
        for idx, item in enumerate(raw):
            if not isinstance(item, dict):
                errors.append(
                    f"Catalogue error ([{idx}]): expected object, got {type(item).__name__}"
                )
                continue
            name = item.get("name", item.get("title", item.get("product")))
            price = item.get("price", item.get("cost"))
            add_product(name, price, f"[{idx}]")
    else:
        errors.append(
            f"Catalogue error: expected JSON object or array, got {type(raw).__name__}"
        )

    return catalogue, errors


def parse_sales(raw: Any) -> Tuple[List[List[LineItem]], List[str]]:
    """
    Parse sales records into a list of sales, each sale is a list of LineItem.

    Supports common JSON shapes:
      A) [{"items": [{"product": "A", "quantity": 2}, ...]}, ...]
      B) [{"product": "A", "quantity": 2}, {"product": "B", "quantity": 1}]  (single sale)
      C) {"sales": [...]}  (wrap)
      D) [{"items": [{"name": "A", "qty": 2}, ...]}, ...] (alternate keys)
    """
    errors: List[str] = []

    def parse_item(item: Any, context: str) -> Optional[LineItem]:
        if not isinstance(item, dict):
            errors.append(
                f"Sales error ({context}): expected object, got {type(item).__name__}"
            )
            return None

        product = item.get("product", item.get("name", item.get("title")))
        quantity = item.get("quantity", item.get("qty", item.get("count", 1)))

        if not isinstance(product, str) or not product.strip():
            errors.append(f"Sales error ({context}): invalid product: {product!r}")
            return None

        qty_num = _as_float(quantity)
        if qty_num is None or qty_num <= 0:
            errors.append(
                f"Sales error ({context}): invalid quantity for {product!r}: {quantity!r}"
            )
            return None

        return LineItem(product=product.strip(), quantity=qty_num)

    def parse_sale(sale: Any, context: str) -> Optional[List[LineItem]]:
        if isinstance(sale, dict) and "items" in sale:
            items = sale.get("items")
            if not isinstance(items, list):
                errors.append(
                    f"Sales error ({context}.items): expected array, got {type(items).__name__}"
                )
                return None
            parsed: List[LineItem] = []
            for jdx, item in enumerate(items):
                li = parse_item(item, f"{context}.items[{jdx}]")
                if li is not None:
                    parsed.append(li)
            return parsed

        # If it's a dict that looks like a single line item, treat as one-item sale
        if isinstance(sale, dict) and (
            "product" in sale or "name" in sale or "title" in sale
        ):
            li = parse_item(sale, context)
            return [li] if li is not None else []

        errors.append(
            f"Sales error ({context}): expected sale object, got {type(sale).__name__}"
        )
        return None

    # Unwrap {"sales": [...]}
    if isinstance(raw, dict) and "sales" in raw:
        raw = raw["sales"]

    sales: List[List[LineItem]] = []

    if isinstance(raw, list):
        # Detect if list is a list of line items (single sale) or list of sales
        if raw and all(isinstance(x, dict) and ("product" in x or "name" in x) for x in raw):
            # Single sale as list of items
            one_sale: List[LineItem] = []
            for idx, item in enumerate(raw):
                li = parse_item(item, f"sales[{idx}]")
                if li is not None:
                    one_sale.append(li)
            sales.append(one_sale)
        else:
            for idx, sale in enumerate(raw):
                parsed_sale = parse_sale(sale, f"sales[{idx}]")
                if parsed_sale is not None:
                    sales.append(parsed_sale)
    else:
        errors.append(
            f"Sales error: expected JSON array (or object with 'sales'), got {type(raw).__name__}"
        )

    return sales, errors


def compute_totals(
    catalogue: Dict[str, float],
    sales: Iterable[List[LineItem]],
) -> Tuple[float, List[str], List[Tuple[int, float]]]:
    """
    Compute grand total. Returns:
      - grand_total
      - errors
      - per_sale_totals: list of (sale_index, sale_total)
    """
    errors: List[str] = []
    per_sale_totals: List[Tuple[int, float]] = []
    grand_total = 0.0

    for sale_idx, sale in enumerate(sales, start=1):
        sale_total = 0.0
        for item in sale:
            price = catalogue.get(item.product)
            if price is None:
                errors.append(
                    f"Pricing error (sale {sale_idx}): product not found in catalogue: {item.product!r}"
                )
                continue
            sale_total += price * item.quantity
        per_sale_totals.append((sale_idx, sale_total))
        grand_total += sale_total

    return grand_total, errors, per_sale_totals


def format_report(
    catalogue_path: str,
    sales_path: str,
    per_sale_totals: List[Tuple[int, float]],
    grand_total: float,
    errors: List[str],
    elapsed_seconds: float,
) -> str:
    """Create a human-readable report."""
    lines: List[str] = []
    lines.append("SALES RESULTS")
    lines.append("=" * 60)
    lines.append(f"Catalogue file : {catalogue_path}")
    lines.append(f"Sales file     : {sales_path}")
    lines.append("-" * 60)
    lines.append("Per-sale totals:")
    if per_sale_totals:
        for sale_idx, sale_total in per_sale_totals:
            lines.append(f"  Sale {sale_idx:>4}: {sale_total:,.2f}")
    else:
        lines.append("  (No valid sales found)")
    lines.append("-" * 60)
    lines.append(f"GRAND TOTAL: {grand_total:,.2f}")
    lines.append(f"Elapsed time: {elapsed_seconds:.6f} seconds")
    lines.append("=" * 60)

    if errors:
        lines.append("")
        lines.append("WARNINGS / ERRORS (execution continued):")
        lines.append("-" * 60)
        for msg in errors:
            lines.append(f"- {msg}")

    lines.append("")
    return "\n".join(lines)


def write_text_file(path: Union[str, Path], content: str) -> Optional[str]:
    """Write content to a text file. Return error message if any."""
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
    except OSError as exc:
        return f"ERROR: Could not write results file {path}: {exc}"
    return None


def main(argv: List[str]) -> int:
    start = time.perf_counter()

    if len(argv) != 3:
        eprint(
            "Usage:\n"
            "  python computeSales.py priceCatalogue.json salesRecord.json"
        )
        return 2

    catalogue_path = argv[1]
    sales_path = argv[2]

    all_errors: List[str] = []

    raw_catalogue = load_json(catalogue_path)
    raw_sales = load_json(sales_path)

    if raw_catalogue is None or raw_sales is None:
        # Still produce a report with elapsed time and errors.
        if raw_catalogue is None:
            all_errors.append("Fatal: could not load catalogue JSON.")
        if raw_sales is None:
            all_errors.append("Fatal: could not load sales JSON.")

        elapsed = time.perf_counter() - start
        report = format_report(
            catalogue_path=catalogue_path,
            sales_path=sales_path,
            per_sale_totals=[],
            grand_total=0.0,
            errors=all_errors,
            elapsed_seconds=elapsed,
        )
        print(report)
        write_err = write_text_file(RESULTS_FILE_NAME, report)
        if write_err:
            eprint(write_err)
        return 1

    catalogue, catalogue_errors = parse_catalogue(raw_catalogue)
    sales, sales_errors = parse_sales(raw_sales)
    all_errors.extend(catalogue_errors)
    all_errors.extend(sales_errors)

    grand_total, pricing_errors, per_sale_totals = compute_totals(catalogue, sales)
    all_errors.extend(pricing_errors)

    elapsed = time.perf_counter() - start

    report = format_report(
        catalogue_path=catalogue_path,
        sales_path=sales_path,
        per_sale_totals=per_sale_totals,
        grand_total=grand_total,
        errors=all_errors,
        elapsed_seconds=elapsed,
    )

    print(report)
    write_err = write_text_file(RESULTS_FILE_NAME, report)
    if write_err:
        eprint(write_err)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
