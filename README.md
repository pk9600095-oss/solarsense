# SolarSense

SolarSense is a physics-based rooftop solar energy and savings optimizer for Chennai.

Users can enter rooftop area, panel tilt, orientation, shading, panel efficiency, electricity tariff, and monthly electricity usage. The application estimates solar generation, financial savings, payback period, and a 25-year cash-flow projection.

## Features

- Estimates daily and annual solar energy generation
- Calculates electricity savings and payback period
- Compares panel tilt and compass orientation
- Displays a 25-year cash-flow projection
- Provides a physics explanation of the underlying model

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
