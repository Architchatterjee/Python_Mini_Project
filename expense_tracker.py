"""
Personal Expense Tracker & Analysis System
------------------------------------------
Record daily expenses, store them in a CSV file, analyse spending with
Pandas and visualise it with Matplotlib.

Run:  python expense_tracker.py
Needs: pip install pandas matplotlib
"""

import math
import os
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.csv")
COLUMNS = ["Date", "Category", "Amount", "Description"]
CATEGORIES = ["Food", "Travel", "Education", "Shopping", "Entertainment", "Other"]
CURRENCY = "Rs."
DATE_FORMATS = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"]  # accepted input formats


# ----------------------------------------------------------------------------
# File handling (save / retrieve)
# ----------------------------------------------------------------------------
def load_expenses() -> pd.DataFrame:
    """Load expenses from the CSV file (empty table if none exists yet)."""
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=COLUMNS).astype(
            {"Amount": float, "Category": str, "Description": str}
        )
    try:
        df = pd.read_csv(DATA_FILE)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
        df["Description"] = df["Description"].fillna("").astype(str)
        df = df.dropna(subset=["Date", "Amount"])  # drop corrupted rows
        return df[COLUMNS].reset_index(drop=True)
    except Exception as exc:
        print(f"Could not read {DATA_FILE}: {exc}. Starting with an empty list.")
        return pd.DataFrame(columns=COLUMNS)


def save_expenses(df: pd.DataFrame) -> None:
    """Write expenses to the CSV file."""
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(DATA_FILE, index=False)


# ----------------------------------------------------------------------------
# Input helpers (with validation)
# ----------------------------------------------------------------------------
def parse_date(text: str):
    """Return a datetime for valid text, otherwise None."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    return None


def ask_date() -> datetime:
    while True:
        text = input("Date (YYYY-MM-DD or DD-MM-YYYY, Enter = today): ").strip()
        if not text:
            return datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        date = parse_date(text)
        if date is None:
            print("  Invalid date. Example: 2026-10-07 or 07-10-2026")
        elif date > datetime.today():
            print("  Date cannot be in the future.")
        else:
            return date


def ask_amount() -> float:
    while True:
        text = input("Amount: ").strip().replace(",", "")
        try:
            amount = float(text)
        except ValueError:
            print("  Invalid amount. Please enter a number, e.g. 250.50")
            continue
        if not math.isfinite(amount) or amount <= 0:
            print("  Amount must be a positive number.")
            continue
        return round(amount, 2)


def ask_category() -> str:
    print("Categories:")
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"  {i}. {cat}")
    while True:
        choice = input("Choose category (number or name): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(CATEGORIES):
            return CATEGORIES[int(choice) - 1]
        for cat in CATEGORIES:
            if choice.lower() == cat.lower():
                return cat
        print("  Invalid choice.")


# ----------------------------------------------------------------------------
# Core features
# ----------------------------------------------------------------------------
def add_expense(df: pd.DataFrame) -> pd.DataFrame:
    print("\n--- Add Expense ---")
    date = ask_date()
    category = ask_category()
    amount = ask_amount()
    description = input("Description (optional): ").strip()

    new_row = pd.DataFrame(
        [{"Date": date, "Category": category, "Amount": amount, "Description": description}]
    )
    df = new_row.copy() if df.empty else pd.concat([df, new_row], ignore_index=True)
    save_expenses(df)
    print(f"Saved: {category} - {CURRENCY}{amount:,.2f} on {date:%Y-%m-%d}")
    return df


def has_data(df: pd.DataFrame) -> bool:
    if df.empty:
        print("\nNo expenses recorded yet. Add some first.")
        return False
    return True


def show_table(df: pd.DataFrame) -> None:
    view = df.copy()
    view["Date"] = pd.to_datetime(view["Date"]).dt.strftime("%Y-%m-%d")
    view["Amount"] = view["Amount"].map(lambda x: f"{x:,.2f}")
    print(view.to_string(index=False))


def view_expenses(df: pd.DataFrame) -> None:
    if not has_data(df):
        return
    print("\n--- All Expenses ---")
    show_table(df)


def sort_expenses(df: pd.DataFrame) -> None:
    if not has_data(df):
        return
    print("\nSort by:  1. Date   2. Amount   3. Category")
    key = {"1": "Date", "2": "Amount", "3": "Category"}.get(input("Choice: ").strip())
    if key is None:
        print("Invalid choice.")
        return
    order = input("Ascending or descending? (a/d): ").strip().lower()
    result = df.sort_values(key, ascending=(order != "d"))
    print(f"\n--- Expenses sorted by {key} ---")
    show_table(result)


def summary(df: pd.DataFrame) -> None:
    if not has_data(df):
        return
    print("\n=========== SPENDING SUMMARY ===========")
    print(f"Number of expenses   : {len(df)}")
    print(f"Total expenditure    : {CURRENCY}{df['Amount'].sum():,.2f}")
    print(f"Average expenditure  : {CURRENCY}{df['Amount'].mean():,.2f} per expense")

    # Monthly
    monthly = df.groupby(pd.to_datetime(df["Date"]).dt.to_period("M"))["Amount"].sum()
    print("\nMonthly expenditure:")
    for month, total in monthly.items():
        print(f"  {month}  {CURRENCY}{total:,.2f}")
    print(f"  (average per month: {CURRENCY}{monthly.mean():,.2f})")

    # Category-wise
    by_cat = df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
    grand = by_cat.sum()
    print("\nCategory-wise expenditure:")
    for cat, total in by_cat.items():
        print(f"  {cat:<15} {CURRENCY}{total:>12,.2f}  ({total / grand * 100:5.1f}%)")

    # Highest / lowest
    hi = df.loc[df["Amount"].idxmax()]
    lo = df.loc[df["Amount"].idxmin()]
    print("\nHighest expense:")
    print(f"  {CURRENCY}{hi['Amount']:,.2f} | {hi['Category']} | {hi['Date']:%Y-%m-%d} | {hi['Description']}")
    print("Lowest expense:")
    print(f"  {CURRENCY}{lo['Amount']:,.2f} | {lo['Category']} | {lo['Date']:%Y-%m-%d} | {lo['Description']}")
    print("=" * 40)


def monthly_report(df: pd.DataFrame) -> None:
    """Detailed report for one chosen month."""
    if not has_data(df):
        return
    text = input("Month to report (YYYY-MM, Enter = current month): ").strip()
    text = text or datetime.today().strftime("%Y-%m")
    try:
        period = pd.Period(text, freq="M")
    except Exception:
        print("Invalid month. Use the format YYYY-MM, e.g. 2026-10")
        return
    subset = df[pd.to_datetime(df["Date"]).dt.to_period("M") == period]
    if subset.empty:
        print(f"No expenses found for {period}.")
        return
    print(f"\n--- Report for {period} ---")
    print(f"Total   : {CURRENCY}{subset['Amount'].sum():,.2f}")
    print(f"Average : {CURRENCY}{subset['Amount'].mean():,.2f}")
    print(subset.groupby("Category")["Amount"].sum().sort_values(ascending=False)
          .map(lambda x: f"{CURRENCY}{x:,.2f}").to_string())


# ----------------------------------------------------------------------------
# Visualisation (Matplotlib)
# ----------------------------------------------------------------------------
def finish_plot(name: str) -> None:
    plt.tight_layout()
    path = os.path.join(os.path.dirname(DATA_FILE), name)
    plt.savefig(path, dpi=120)
    print(f"Chart saved as {path}")
    plt.show()


def bar_chart(df: pd.DataFrame) -> None:
    by_cat = df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
    plt.figure(figsize=(8, 5))
    bars = plt.bar(by_cat.index, by_cat.values, color="steelblue")
    plt.bar_label(bars, fmt="%.0f")
    plt.title("Expenditure by Category")
    plt.xlabel("Category")
    plt.ylabel(f"Amount ({CURRENCY})")
    plt.xticks(rotation=30)
    finish_plot("chart_bar.png")


def pie_chart(df: pd.DataFrame) -> None:
    by_cat = df.groupby("Category")["Amount"].sum()
    plt.figure(figsize=(7, 7))
    plt.pie(by_cat.values, labels=by_cat.index, autopct="%1.1f%%", startangle=90)
    plt.title("Share of Spending By Category")
    finish_plot("chart_pie.png")


def line_plot(df: pd.DataFrame) -> None:
    monthly = df.groupby(pd.to_datetime(df["Date"]).dt.to_period("M"))["Amount"].sum()
    plt.figure(figsize=(9, 5))
    plt.plot(monthly.index.astype(str), monthly.values, marker="o", color="darkgreen")
    for x, y in zip(monthly.index.astype(str), monthly.values):
        plt.annotate(f"{y:,.0f}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center")
    plt.title("Monthly Expenditure Trend")
    plt.xlabel("Month")
    plt.ylabel(f"Amount ({CURRENCY})")
    plt.grid(alpha=0.3)
    plt.xticks(rotation=30)
    finish_plot("chart_line.png")


def histogram(df: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 5))
    plt.hist(df["Amount"], bins=min(10, max(len(df), 1)), color="coral", edgecolor="black")
    plt.title("Distribution of Expense Amounts")
    plt.xlabel(f"Amount ({CURRENCY})")
    plt.ylabel("Number of expenses")
    finish_plot("chart_histogram.png")


def charts_menu(df: pd.DataFrame) -> None:
    if not has_data(df):
        return
    print("\n--- Charts ---")
    print("1. Bar chart (category-wise)")
    print("2. Pie chart (category share)")
    print("3. Line plot (monthly trend)")
    print("4. Histogram (amount distribution)")
    actions = {"1": bar_chart, "2": pie_chart, "3": line_plot, "4": histogram}
    action = actions.get(input("Choice: ").strip())
    if action:
        action(df)
    else:
        print("Invalid choice.")


# ----------------------------------------------------------------------------
# Main menu
# ----------------------------------------------------------------------------
MENU = """
=========== EXPENSE TRACKER ===========
 1. Add expense
 2. View all expenses
 3. Sort expenses
 4. Spending summary (total, monthly, category, average, highest/lowest)
 5. Report for a specific month
 6. Charts
 0. Exit
=======================================
"""


def main() -> None:
    df = load_expenses()
    print(f"Loaded {len(df)} expense record(s) from {DATA_FILE}")
    while True:
        print(MENU)
        choice = input("Select an option: ").strip()
        if choice == "1":
            df = add_expense(df)
        elif choice == "2":
            view_expenses(df)
        elif choice == "3":
            sort_expenses(df)
        elif choice == "4":
            summary(df)
        elif choice == "5":
            monthly_report(df)
        elif choice == "6":
            charts_menu(df)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid option, please try again.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
