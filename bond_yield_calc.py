#!/usr/bin/env python3
# Copyright 2026 akocis. All rights reserved.

"""Bond yield calculator CLI tool."""

import argparse
import cmd
import math
import os
import readline
import shlex
import sys
from datetime import date, datetime
from pathlib import Path


FACE_VALUE = 1000.0  # Standard bond face value
HISTORY_FILE = os.path.join(Path.home(), ".bond_yield_history")


class ParseError(Exception):
    pass


class ReplArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that raises instead of calling sys.exit."""

    def exit(self, status=0, message=None):
        if message:
            raise ParseError(message.strip())
        raise ParseError()

    def error(self, message):
        raise ParseError(message)


def parse_number(value):
    """Parse a number that may contain commas as thousands separators."""
    return float(value.replace(",", ""))


def parse_int_number(value):
    """Parse an integer that may contain commas as thousands separators."""
    return int(value.replace(",", ""))


def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: '{date_str}'. Use YYYY-MM-DD."
        )


CALC_OPTIONS = [
    "-p", "--purchase-date",
    "-a", "--purchase-price",
    "-A", "--purchase-price-total",
    "-n", "--bonds",
    "-m", "--maturity-date",
    "-s", "--sell-price",
    "-S", "--sell-price-total",
    "-d", "--sell-date",
    "--face-value",
]


def build_calc_parser(repl_mode=False):
    cls = ReplArgumentParser if repl_mode else argparse.ArgumentParser
    parser = cls(
        prog="calc" if repl_mode else None,
        description="Bond yield calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s -p 2025-01-15 -a 980 -n 10 -m 2026-01-15 -s 995
  %(prog)s -p 2025-01-15 -A 9800 -n 10 -m 2026-01-15 -S 9950
  %(prog)s -p 2025-01-15 -a 980 -n 10 -m 2026-01-15 -s 995 -d 2025-07-15
""",
    )
    parser.add_argument(
        "-p", "--purchase-date", type=parse_date, required=True,
        help="Bond purchase date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "-a", "--purchase-price", type=parse_number,
        help="Purchase price per bond (dollar amount)",
    )
    parser.add_argument(
        "-A", "--purchase-price-total", type=parse_number,
        help="Total purchase price for all bonds (divided by number of bonds)",
    )
    parser.add_argument(
        "-n", "--bonds", type=parse_int_number, required=True,
        help="Number of bonds",
    )
    parser.add_argument(
        "-m", "--maturity-date", type=parse_date, required=True,
        help="Bond maturity date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "-s", "--sell-price", type=parse_number,
        help="Bond sell price per bond",
    )
    parser.add_argument(
        "-S", "--sell-price-total", type=parse_number,
        help="Total sell price for all bonds (divided by number of bonds)",
    )
    parser.add_argument(
        "-d", "--sell-date", type=parse_date, default=date.today(),
        help="Bond sell date (YYYY-MM-DD, defaults to today)",
    )
    parser.add_argument(
        "--face-value", type=parse_number, default=FACE_VALUE,
        help=f"Bond face value (default: {FACE_VALUE})",
    )
    return parser


def validate_args(args, parser):
    if args.purchase_price and args.purchase_price_total:
        parser.error("Use either --purchase-price (-a) or --purchase-price-total (-A), not both")
    if not args.purchase_price and not args.purchase_price_total:
        parser.error("Either --purchase-price (-a) or --purchase-price-total (-A) is required")
    if args.sell_price and args.sell_price_total:
        parser.error("Use either --sell-price (-s) or --sell-price-total (-S), not both")
    if not args.sell_price and not args.sell_price_total:
        parser.error("Either --sell-price (-s) or --sell-price-total (-S) is required")

    if args.purchase_price_total:
        args.purchase_price = args.purchase_price_total / args.bonds
    if args.sell_price_total:
        args.sell_price = args.sell_price_total / args.bonds

    if args.purchase_date >= args.maturity_date:
        parser.error("Purchase date must be before maturity date")
    if args.purchase_date > args.sell_date:
        parser.error("Purchase date must be before or equal to sell date")
    if args.bonds < 1:
        parser.error("Number of bonds must be at least 1")
    if args.purchase_price <= 0:
        parser.error("Purchase price must be positive")
    if args.sell_price <= 0:
        parser.error("Sell price must be positive")

    return args


def parse_args():
    parser = build_calc_parser()
    args = parser.parse_args()
    return validate_args(args, parser)


def calculate(args):
    face = args.face_value
    purchase_price = args.purchase_price
    sell_price = args.sell_price
    num_bonds = args.bonds

    days_to_maturity = (args.maturity_date - args.purchase_date).days
    days_held = (args.sell_date - args.purchase_date).days

    total_invested = purchase_price * num_bonds
    total_sell = sell_price * num_bonds

    # --- Annual yield (annualized return if held to maturity) ---
    gain_per_bond_at_maturity = face - purchase_price
    annual_yield_pct = (gain_per_bond_at_maturity / purchase_price) * (365.0 / days_to_maturity) * 100.0
    annual_amount_per_bond = gain_per_bond_at_maturity * (365.0 / days_to_maturity)
    annual_amount_total = annual_amount_per_bond * num_bonds

    # --- Compounding yields ---
    total_return = face / purchase_price
    years_to_maturity = days_to_maturity / 365.0
    compound_annual_pct = (total_return ** (1.0 / years_to_maturity) - 1) * 100.0
    compound_semi_pct = 2.0 * (total_return ** (1.0 / (2.0 * years_to_maturity)) - 1) * 100.0
    compound_quarterly_pct = 4.0 * (total_return ** (1.0 / (4.0 * years_to_maturity)) - 1) * 100.0
    compound_monthly_pct = 12.0 * (total_return ** (1.0 / (12.0 * years_to_maturity)) - 1) * 100.0
    compound_continuous_pct = (math.log(total_return) / years_to_maturity) * 100.0

    # --- Expected yield from purchase to sell date (pro-rated maturity gain) ---
    expected_gain_per_bond = gain_per_bond_at_maturity * (days_held / days_to_maturity) if days_to_maturity > 0 else 0
    expected_yield_pct = (expected_gain_per_bond / purchase_price) * 100.0 if days_held > 0 else 0
    expected_amount_total = expected_gain_per_bond * num_bonds

    # --- Actual yield based on sell price and holding period ---
    actual_gain_per_bond = sell_price - purchase_price
    actual_yield_pct = (actual_gain_per_bond / purchase_price) * 100.0 if days_held > 0 else 0
    actual_amount_total = actual_gain_per_bond * num_bonds

    # --- Actual yield annualized ---
    actual_annual_yield_pct = (actual_gain_per_bond / purchase_price) * (365.0 / days_held) * 100.0 if days_held > 0 else 0

    # --- Delta between actual selling yield and expected yield ---
    delta_yield_pct = actual_yield_pct - expected_yield_pct
    delta_amount_per_bond = actual_gain_per_bond - expected_gain_per_bond
    delta_amount_total = delta_amount_per_bond * num_bonds

    return {
        "face": face,
        "purchase_price": purchase_price,
        "sell_price": sell_price,
        "num_bonds": num_bonds,
        "total_invested": total_invested,
        "total_sell": total_sell,
        "days_to_maturity": days_to_maturity,
        "days_held": days_held,
        "annual_yield_pct": annual_yield_pct,
        "annual_amount_per_bond": annual_amount_per_bond,
        "annual_amount_total": annual_amount_total,
        "compound_annual_pct": compound_annual_pct,
        "compound_semi_pct": compound_semi_pct,
        "compound_quarterly_pct": compound_quarterly_pct,
        "compound_monthly_pct": compound_monthly_pct,
        "compound_continuous_pct": compound_continuous_pct,
        "expected_yield_pct": expected_yield_pct,
        "expected_gain_per_bond": expected_gain_per_bond,
        "expected_amount_total": expected_amount_total,
        "actual_yield_pct": actual_yield_pct,
        "actual_gain_per_bond": actual_gain_per_bond,
        "actual_amount_total": actual_amount_total,
        "actual_annual_yield_pct": actual_annual_yield_pct,
        "delta_yield_pct": delta_yield_pct,
        "delta_amount_per_bond": delta_amount_per_bond,
        "delta_amount_total": delta_amount_total,
    }


USE_COLOR = sys.stdout.isatty()

BOLD = "\033[1m" if USE_COLOR else ""
GREEN = "\033[32m" if USE_COLOR else ""
RED = "\033[31m" if USE_COLOR else ""
RESET = "\033[0m" if USE_COLOR else ""

LABEL_W = 23  # width of label column


def fmt(val):
    """Format a dollar amount."""
    return f"${val:,.2f}"


def pct(val):
    """Format a percentage."""
    return f"{val:+.4f}%" if val != 0 else f"{val:.4f}%"


def row(label, value, suffix=""):
    """Print a row with aligned label and value columns."""
    text = f"{suffix}" if suffix else ""
    print(f"  {label:<{LABEL_W}} {value}{text}")


def row_total(label, value, suffix=""):
    """Print a bold total row."""
    text = f"{suffix}" if suffix else ""
    print(f"  {BOLD}{label:<{LABEL_W}} {value}{text}{RESET}")


def delta_color(val):
    """Return color code based on sign."""
    if val > 0:
        return GREEN
    elif val < 0:
        return RED
    return ""


def row_delta(label, value):
    """Print a delta row with color."""
    color = delta_color(float(value.replace("$", "").replace(",", "").replace("%", "").replace("+", "")))
    print(f"  {BOLD}{color}{label:<{LABEL_W}} {value}{RESET}")


def print_results(args, r):
    n = r["num_bonds"]
    sep = "-" * 62
    total_label = f"Total ({n} bonds):"

    print(sep)
    print(f"  {BOLD}BOND YIELD CALCULATOR{RESET}")
    print(sep)
    row("Face value:", f"{fmt(r['face'])} per bond")
    row("Purchase price:", f"{fmt(r['purchase_price'])} per bond")
    row("Number of bonds:", f"{n}")
    row_total("Total invested:", fmt(r['total_invested']))
    row("Purchase date:", f"{args.purchase_date}")
    row("Maturity date:", f"{args.maturity_date}  ({r['days_to_maturity']} days)")
    row("Sell date:", f"{args.sell_date}  ({r['days_held']} days held)")
    row("Sell price:", f"{fmt(r['sell_price'])} per bond")
    row_total("Total sell price:", fmt(r['total_sell']))
    print(sep)

    print(f"\n  ANNUAL YIELD (simple, if held to maturity)")
    print(sep)
    row("Yield:", f"{r['annual_yield_pct']:.4f}%")
    row("Amount per bond:", f"{fmt(r['annual_amount_per_bond'])} / year")
    row_total(total_label, f"{fmt(r['annual_amount_total'])} / year")
    print(sep)

    print(f"\n  COMPOUNDING YIELD (annualized, if held to maturity)")
    print(sep)
    row("Annual:", f"{r['compound_annual_pct']:.4f}%")
    row("Semi-annual:", f"{r['compound_semi_pct']:.4f}%")
    row("Quarterly:", f"{r['compound_quarterly_pct']:.4f}%")
    row("Monthly:", f"{r['compound_monthly_pct']:.4f}%")
    row("Continuous:", f"{r['compound_continuous_pct']:.4f}%")
    print(sep)

    print(f"\n  EXPECTED YIELD (pro-rated to sell date, {r['days_held']} days)")
    print(sep)
    row("Yield:", f"{r['expected_yield_pct']:.4f}%")
    row("Amount per bond:", fmt(r['expected_gain_per_bond']))
    row_total(total_label, fmt(r['expected_amount_total']))
    print(sep)

    print(f"\n  ACTUAL YIELD (based on sell price, {r['days_held']} days held)")
    print(sep)
    row("Yield:", f"{r['actual_yield_pct']:.4f}%")
    row("Annualized yield:", f"{r['actual_annual_yield_pct']:.4f}%")
    row("Amount per bond:", fmt(r['actual_gain_per_bond']))
    row_total(total_label, fmt(r['actual_amount_total']))
    print(sep)

    print(f"\n  DELTA (actual sell vs expected)")
    print(sep)
    row_delta("Yield difference:", pct(r['delta_yield_pct']))
    row_delta("Amount per bond:", fmt(r['delta_amount_per_bond']))
    row_delta(total_label, fmt(r['delta_amount_total']))
    print(sep)


class BondRepl(cmd.Cmd):
    intro = (
        f"\n{BOLD}Bond Yield Calculator — Interactive Mode{RESET}\n"
        "Type 'calc' with options to compute, 'help' for commands, 'quit' to exit.\n"
        "Example: calc -p 2025-01-15 -a 980 -n 10 -m 2026-01-15 -s 995\n"
    )
    prompt = f"\001{BOLD}\002bond>\001{RESET}\002 " if USE_COLOR else "bond> "

    REPL_COMMANDS = ["calc", "help", "quit", "exit"]

    def preloop(self):
        try:
            readline.read_history_file(HISTORY_FILE)
        except FileNotFoundError:
            pass
        readline.set_history_length(1000)
        readline.parse_and_bind("tab: complete")

    def postloop(self):
        try:
            readline.write_history_file(HISTORY_FILE)
        except OSError:
            pass

    def do_calc(self, line):
        """Calculate bond yield. Usage: calc [options] (same flags as CLI mode)"""
        try:
            argv = shlex.split(line)
        except ValueError as e:
            print(f"Error: {e}")
            return

        parser = build_calc_parser(repl_mode=True)
        try:
            args = parser.parse_args(argv)
            args = validate_args(args, parser)
        except ParseError as e:
            if str(e):
                print(f"Error: {e}")
            return

        results = calculate(args)
        print_results(args, results)

    def complete_calc(self, text, line, begidx, endidx):
        return [o for o in CALC_OPTIONS if o.startswith(text)]

    def do_quit(self, _line):
        """Exit the calculator."""
        return True

    def do_exit(self, _line):
        """Exit the calculator."""
        return True

    do_EOF = do_quit

    def emptyline(self):
        pass

    def default(self, line):
        # Treat bare input as implicit 'calc' command
        self.do_calc(line)

    def completedefault(self, text, line, begidx, endidx):
        return self.complete_calc(text, line, begidx, endidx)


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-i", "--interactive"):
        BondRepl().cmdloop()
    elif len(sys.argv) == 1 and sys.stdin.isatty():
        BondRepl().cmdloop()
    else:
        args = parse_args()
        results = calculate(args)
        print_results(args, results)


if __name__ == "__main__":
    main()
