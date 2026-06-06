# ELEC1301 Wind Forecasting & Astrocrash Mini Project

A university mini-project combining data analysis, forecasting, and game development in Python.

The project contains two main parts:

1. **Wind-generation analytics and forecasting** using historical energy time-series data.
2. **Astrocrash**, a Pygame arcade-style asteroid game refactor.

## Project Structure

```text
src/
  wind_forecasting.py   Python script for wind-generation analysis and ARIMA forecasting
  astrocrash.py         Pygame asteroid game

data/
  question_1/           LIV and spectra datasets
  question_2/           Wind-generation time-series dataset
  question_3/           Airline network datasets
  question_4/           Original AstroCrash reference script

outputs/
  figures/              Saved output plots from the wind-generation analysis

assets/
  astrocrash_demo.mp4   Short gameplay/demo video

reports/
  final_report.pdf      Final submitted project report
```

## Tools and Technologies

- Python
- NumPy
- Matplotlib
- Statsmodels / ARIMA
- Pygame
- CSV data processing
- Time-series analysis
- Game physics and collision detection

## How to Run

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the wind-generation analysis:

```bash
python src/wind_forecasting.py --country DE
```

Run the Astrocrash game:

```bash
python src/astrocrash.py
```

## Key Skills Demonstrated

- Data loading and preprocessing
- Time-series aggregation
- ARIMA forecasting
- Data visualisation
- Python game development
- Modular programming
- Collision detection and simple game physics
- Technical reporting

## Notes

This repository was cleaned for portfolio use. Draft documents, duplicate ZIPs, assessment templates, and temporary files were removed.
