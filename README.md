# Bond Yield Calculator

Command-line tool for calculating bond yields, comparing actual sell returns against expected maturity-based returns.

## Requirements

Python 3.7+

## Usage

### CLI Mode

```
python3 bond_yield.py [options]
```

### Interactive (REPL) Mode

Run with no arguments or with `-i` / `--interactive`:

```
python3 bond_yield.py
python3 bond_yield.py -i
```

In interactive mode:
- Type `calc` followed by options, or just type options directly
- Press Tab to autocomplete flags
- Use arrow keys to navigate command history (persisted across sessions in `~/.bond_yield_history`)
- Type `help`, `quit`, or `exit`

## Options

| Flag | Long form | Description |
|------|-----------|-------------|
| `-p` | `--purchase-date` | Bond purchase date (YYYY-MM-DD) |
| `-a` | `--purchase-price` | Purchase price per bond |
| `-A` | `--purchase-price-total` | Total purchase price for all bonds |
| `-n` | `--bonds` | Number of bonds |
| `-m` | `--maturity-date` | Bond maturity date (YYYY-MM-DD) |
| `-s` | `--sell-price` | Sell price per bond |
| `-S` | `--sell-price-total` | Total sell price for all bonds |
| `-d` | `--sell-date` | Sell date (YYYY-MM-DD, defaults to today) |
|      | `--face-value` | Bond face value (default: 1000) |

- Use `-a` or `-A` (not both) for purchase price
- Use `-s` or `-S` (not both) for sell price
- All numeric inputs accept commas as thousands separators (e.g. `9,700`)

## Examples

Per-bond pricing:

```
python3 bond_yield.py -p 2025-01-15 -a 980 -n 10 -m 2026-01-15 -s 995
```

Total pricing with explicit sell date:

```
python3 bond_yield.py -p 2025-01-15 -A 9,800 -n 10 -m 2026-01-15 -S 9,950 -d 2025-07-15
```

Interactive mode:

```
$ python3 bond_yield.py
bond> calc -p 2025-06-15 -a 970 -n 10 -m 2026-06-15 -s 990
bond> -p 2025-06-15 -A 9,700 -n 10 -m 2026-06-15 -S 9,900
```

## Output

The calculator displays four sections:

1. **Annual Yield** -- annualized return assuming the bond is held to maturity
2. **Expected Yield** -- pro-rated maturity gain for the actual holding period (purchase date to sell date)
3. **Actual Yield** -- real gain based on sell price over the holding period, plus its annualized rate
4. **Delta** -- difference between actual and expected yield, shown in percentage and dollar amount (color-coded green/red when output is a terminal)
