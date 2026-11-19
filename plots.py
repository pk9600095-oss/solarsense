import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from physics import MONTHS

ORANGE, BLUE, GREEN, GREY = "#F28C28", "#2E6FBA", "#2E9E5B", "#888888"

def monthly_chart(kwh, usage):
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.bar(MONTHS, kwh, color=ORANGE, label="Solar generation")
    ax.plot(MONTHS, usage, color=BLUE, marker="o", label="Your usage")
    ax.set_ylabel("Energy (kWh / month)"); ax.set_title("Monthly solar generation vs. consumption")
    ax.legend(); ax.grid(alpha=.25); fig.tight_layout(); return fig

def daily_profile_chart(t, profiles, month_idx):
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.fill_between(t, profiles[month_idx], color=ORANGE, alpha=.45)
    ax.plot(t, profiles[month_idx], color=ORANGE)
    ax.set_xlim(5, 19); ax.set_xlabel("Solar time (hours)"); ax.set_ylabel("Power P (kW)")
    ax.set_title(f"Typical day power output - {MONTHS[month_idx]}"); ax.grid(alpha=.25)
    fig.tight_layout(); return fig

def heatmap_chart(tilts, azs, grid, best_tilt, best_az, cur_tilt, cur_az):
    fig, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(grid, origin="lower", aspect="auto", cmap="YlOrRd",
                   extent=[azs[0] - 7.5, azs[-1] + 7.5, tilts[0] - 1, tilts[-1] + 1])
    ax.plot(best_az, best_tilt, "k*", ms=16, label=f"Best: {best_tilt} deg tilt")
    ax.plot(cur_az, cur_tilt, "wo", mec="k", ms=9, label="Your setting")
    ax.set_xlabel("Azimuth from South (deg)   [-90 = East, 0 = South, +90 = West]")
    ax.set_ylabel("Tilt angle (deg)"); ax.set_title("Annual energy (kWh) for every tilt / orientation")
    fig.colorbar(im, ax=ax, label="kWh / year"); ax.legend(loc="lower right"); fig.tight_layout(); return fig

def cashflow_chart(cash, payback):
    yrs = np.arange(1, len(cash) + 1)
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.plot(yrs, cash / 1e5, color=GREEN, lw=2); ax.axhline(0, color=GREY, lw=1)
    if payback: ax.axvline(payback, color=BLUE, ls="--", label=f"Payback = {payback:.1f} yr"); ax.legend()
    ax.set_xlabel("Year"); ax.set_ylabel("Cumulative net savings (Rs lakh)")
    ax.set_title("25-year cash flow"); ax.grid(alpha=.25); fig.tight_layout(); return fig

def sun_path_chart(n, tilt, surf_az, sky):
    from physics import cos_incidence, solar_position
    t = np.arange(5, 19, .1)
    sin_alt, _, _ = solar_position(n, t)
    cos_t = cos_incidence(n, t, tilt, surf_az)
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.plot(t, np.degrees(np.arcsin(np.clip(sin_alt, -1, 1))), color=ORANGE, label="Sun altitude (deg)")
    ax.plot(t, np.degrees(np.arccos(np.clip(cos_t, -1, 1))), color=BLUE, label="Incidence angle on panel (deg)")
    ax.set_ylim(0, 100); ax.set_xlabel("Solar time (hours)"); ax.set_ylabel("Angle (deg)")
    ax.set_title("Sun altitude and angle of incidence (summer solstice-type day shown for day %d)" % n, fontsize=9)
    ax.legend(); ax.grid(alpha=.25); fig.tight_layout(); return fig
