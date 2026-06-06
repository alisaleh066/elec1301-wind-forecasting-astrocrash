"""Wind generation data analysis and ARIMA forecasting.

This script loads hourly wind-generation data, aggregates it into monthly,
yearly, and quarterly totals, and produces visualisations including an ARIMA
forecast.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.arima.model import ARIMA


def load_data(filename: Path, country: str):
    """Load wind generation data for a specific country code."""
    years, months, days, hours, values = [], [], [], [], []

    with filename.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader)

        column_index = None
        for index, name in enumerate(header):
            if name.startswith(f"{country}_") and name.endswith("_generation_actual"):
                column_index = index
                break

        if column_index is None:
            available = sorted({col.split("_")[0] for col in header if col.endswith("_generation_actual")})
            raise ValueError(f"Country code '{country}' not found. Available examples: {available[:10]}")

        for row in reader:
            if len(row) <= column_index or not row[1]:
                continue

            timestamp = row[1]
            try:
                years.append(int(timestamp[:4]))
                months.append(int(timestamp[5:7]))
                days.append(int(timestamp[8:10]))
                hours.append(int(timestamp[11:13]))
                values.append(float(row[column_index]) if row[column_index] else 0.0)
            except (ValueError, IndexError):
                continue

    return years, months, days, hours, values


def calculate_aggregations(years, months, values):
    """Calculate monthly, yearly, and quarterly totals."""
    monthly = {}
    for year, month, value in zip(years, months, values):
        key = (year, month)
        monthly[key] = monthly.get(key, 0) + value

    sorted_keys = sorted(monthly.keys())
    monthly_years = [key[0] for key in sorted_keys]
    monthly_months = [key[1] for key in sorted_keys]
    monthly_values = [monthly[key] for key in sorted_keys]

    yearly = {}
    for year, value in zip(monthly_years, monthly_values):
        yearly[year] = yearly.get(year, 0) + value

    yearly_years = sorted(yearly.keys())
    yearly_values = [yearly[year] for year in yearly_years]

    quarterly = {}
    for year, month, value in zip(monthly_years, monthly_months, monthly_values):
        quarter = (month - 1) // 3 + 1
        quarterly[(year, quarter)] = quarterly.get((year, quarter), 0) + value

    quarter_keys = sorted(quarterly.keys())
    quarter_labels = [f"{year}-Q{quarter}" for year, quarter in quarter_keys]
    quarter_values = [quarterly[key] for key in quarter_keys]

    return monthly_years, monthly_months, monthly_values, yearly_years, yearly_values, quarter_labels, quarter_values


def stats_text(values) -> str:
    """Return basic descriptive statistics for a sequence of values."""
    if len(values) < 3:
        return "Not enough data"

    values_array = np.array(values)
    mean = np.mean(values_array)
    std = np.std(values_array)
    skew = np.mean((values_array - mean) ** 3) / (std**3) if std else 0
    return f"μ={mean:.2f} σ={std:.2f} γ={skew:.2f}"


def save_or_show(output_dir: Path | None, filename: str, show: bool):
    """Save the current plot and optionally display it."""
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_dir / filename, dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close()


def plot_charts(country: str, data, aggregation_data, output_dir: Path | None, show: bool):
    """Create visualisations for the analysis."""
    years, months, _days, _hours, values = data
    monthly_years, monthly_months, monthly_values, yearly_years, yearly_values, quarter_labels, quarter_values = aggregation_data

    best_year = yearly_years[np.argmax(yearly_values)]
    peak_index = np.argmax(monthly_values)
    peak_year = monthly_years[peak_index]
    peak_month = monthly_months[peak_index]

    split = int(0.9 * len(monthly_values))
    train, test = monthly_values[:split], monthly_values[split:]
    model = ARIMA(train, order=(5, 3, 1)).fit()
    predictions = list(model.forecast(steps=len(test)))

    plt.figure(figsize=(12, 5))
    plt.plot(values, linewidth=1.2)
    ticks, labels, last_year = [], [], None
    for index, year in enumerate(years):
        if year != last_year:
            ticks.append(index)
            labels.append(str(year))
            last_year = year
    plt.xticks(ticks, labels)
    plt.title(f"Hourly Wind Generation — {country}")
    plt.xlabel("Hour Index")
    plt.ylabel("MW")
    plt.text(0.02, 0.95, stats_text(values), transform=plt.gca().transAxes, bbox=dict(facecolor="white", alpha=0.8))
    plt.grid(True)
    save_or_show(output_dir, "01_hourly_wind_generation.png", show)

    month_values = [value for year, month, value in zip(years, months, values) if year == peak_year and month == peak_month]
    if month_values:
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        plt.figure(figsize=(10, 4))
        plt.plot(month_values, linewidth=1.2)
        plt.title(f"{month_names[peak_month - 1]} {peak_year} — {country}")
        plt.xlabel("Hour of Month")
        plt.ylabel("MW")
        plt.text(0.02, 0.95, stats_text(month_values), transform=plt.gca().transAxes, bbox=dict(facecolor="white", alpha=0.8))
        plt.grid(True)
        save_or_show(output_dir, "02_peak_month.png", show)

    plt.figure(figsize=(8, 5))
    plt.bar(yearly_years, yearly_values)
    plt.title(f"Annual Wind Generation Total — {country}")
    plt.xlabel("Year")
    plt.ylabel("MWh")
    plt.text(0.02, 0.95, stats_text(yearly_values), transform=plt.gca().transAxes, bbox=dict(facecolor="white", alpha=0.8))
    plt.grid(axis="y")
    save_or_show(output_dir, "03_annual_total.png", show)

    plt.figure(figsize=(10, 5))
    plt.bar(quarter_labels, quarter_values)
    plt.title(f"Quarterly Wind Generation Total — {country}")
    plt.xlabel("Quarter")
    plt.ylabel("MWh")
    plt.xticks(rotation=45)
    plt.text(0.02, 0.95, stats_text(quarter_values), transform=plt.gca().transAxes, bbox=dict(facecolor="white", alpha=0.8))
    plt.grid(axis="y")
    save_or_show(output_dir, "04_quarterly_total.png", show)

    best_year_quarters = [(label, value) for label, value in zip(quarter_labels, quarter_values) if label.startswith(str(best_year))]
    if best_year_quarters:
        labels, vals = zip(*best_year_quarters)
        plt.figure(figsize=(6, 4))
        plt.bar(labels, vals)
        plt.title(f"Quarterly Breakdown for {best_year} — {country}")
        plt.xlabel("Quarter")
        plt.ylabel("MWh")
        plt.text(0.02, 0.95, stats_text(vals), transform=plt.gca().transAxes, bbox=dict(facecolor="white", alpha=0.8))
        plt.grid(axis="y")
        save_or_show(output_dir, "05_best_year_quarters.png", show)

    plt.figure(figsize=(10, 5))
    plt.plot(range(len(train)), train, label="Train")
    plt.plot(range(len(train), len(train) + len(test)), test, label="Test")
    plt.plot(range(len(train), len(train) + len(test)), predictions, linestyle="--", label="Predicted")
    plt.title(f"ARIMA(5,3,1) Forecast — {country}")
    plt.xlabel("Month Index")
    plt.ylabel("MWh")
    plt.legend()
    plt.grid(True)
    save_or_show(output_dir, "06_arima_forecast.png", show)


def main():
    repo_root = Path(__file__).resolve().parents[1]
    default_data = repo_root / "data" / "question_2" / "time_series_60min_singleindex.csv"
    default_output = repo_root / "outputs" / "figures" / "wind_forecasting_generated"

    parser = argparse.ArgumentParser(description="Wind-generation analytics and ARIMA forecasting")
    parser.add_argument("--data", type=Path, default=default_data, help="Path to the wind-generation CSV dataset")
    parser.add_argument("--country", default="DE", help="Country code to analyse, for example DE")
    parser.add_argument("--output", type=Path, default=default_output, help="Folder for generated plots")
    parser.add_argument("--show", action="store_true", help="Display plots interactively as well as saving them")
    args = parser.parse_args()

    if not args.data.exists():
        raise FileNotFoundError(f"Data file not found: {args.data}")

    data = load_data(args.data, args.country)
    aggregation_data = calculate_aggregations(data[0], data[1], data[4])
    plot_charts(args.country, data, aggregation_data, args.output, args.show)
    print(f"Analysis complete for {args.country}. Plots saved to: {args.output}")


if __name__ == "__main__":
    main()
