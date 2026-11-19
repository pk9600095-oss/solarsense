"""
SolarSense physics engine
Clear-sky solar geometry + irradiance model for rooftop PV (default site: Chennai).
All angles in degrees unless stated.  Surface azimuth is measured from SOUTH
(south = 0, east = -90, west = +90); the UI converts compass bearings to this.
"""
import numpy as np

LAT = 13.08            # Chennai latitude (deg N)
SOLAR_CONST = 1.353    # kW/m^2 (extraterrestrial)
DAYS_IN_MONTH = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MID_DAY = np.array([17, 47, 75, 105, 135, 162, 198, 228, 258, 288, 318, 344])  # Klein's typical day-of-year
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Assumed Chennai monthly sky clearness (fraction of clear-sky irradiance that
# actually arrives after clouds/haze; NE monsoon Oct-Dec is cloudiest). Adjustable in the UI.
SKY_FACTOR = np.array([0.80, 0.85, 0.85, 0.82, 0.78, 0.70, 0.68, 0.68, 0.68, 0.60, 0.55, 0.70])
# Assumed mean daytime ambient temperature (deg C) for Chennai
AMBIENT_C = np.array([27, 28, 30, 33, 35, 34, 33, 32, 32, 30, 28, 27])

SHADING_LOSS = {"None": 0.0, "Light (a few trees/pipes)": 0.10,
                "Moderate (nearby building/tree)": 0.25, "Heavy (shaded for much of the day)": 0.40}


def declination(n):
    """Solar declination (deg) for day-of-year n  (Cooper's equation)."""
    return 23.45 * np.sin(np.radians(360.0 * (284 + n) / 365.0))


def solar_position(n, t_hours, lat=LAT):
    """Return sin(altitude), declination, hour angle for solar time t (hours)."""
    d = np.radians(declination(n))
    phi = np.radians(lat)
    w = np.radians(15.0 * (t_hours - 12.0))
    sin_alt = np.sin(phi) * np.sin(d) + np.cos(phi) * np.cos(d) * np.cos(w)
    return sin_alt, d, w


def cos_incidence(n, t_hours, tilt, surf_az, lat=LAT):
    """cos(theta): angle between sun rays and the panel normal (general tilted-surface equation)."""
    d = np.radians(declination(n))
    phi = np.radians(lat)
    w = np.radians(15.0 * (t_hours - 12.0))
    b = np.radians(tilt)
    g = np.radians(surf_az)
    return (np.sin(d) * np.sin(phi) * np.cos(b)
            - np.sin(d) * np.cos(phi) * np.sin(b) * np.cos(g)
            + np.cos(d) * np.cos(phi) * np.cos(b) * np.cos(w)
            + np.cos(d) * np.sin(phi) * np.sin(b) * np.cos(g) * np.cos(w)
            + np.cos(d) * np.sin(b) * np.sin(g) * np.sin(w))


def irradiance_components(n, t_hours, tilt, surf_az, sky=1.0, albedo=0.2, lat=LAT):
    """
    Plane-of-array irradiance (kW/m^2) = beam + diffuse + ground-reflected.
    Beam from Meinel's air-mass model; diffuse = 10 % of beam (ASHRAE-type simple model).
    """
    sin_alt, d, w = solar_position(n, t_hours, lat)
    sin_alt = np.asarray(sin_alt, dtype=float)
    up = sin_alt > 0.02
    safe = np.where(up, sin_alt, 1.0)
    airmass = 1.0 / safe
    e0 = SOLAR_CONST * (1 + 0.033 * np.cos(np.radians(360.0 * n / 365.0)))
    dni = np.where(up, e0 * 0.7 ** (airmass ** 0.678), 0.0) * sky
    dhi = 0.10 * dni
    cos_t = cos_incidence(n, t_hours, tilt, surf_az, lat)
    b = np.radians(tilt)
    beam = dni * np.clip(cos_t, 0, None)
    diffuse = dhi * (1 + np.cos(b)) / 2
    ghi = dni * sin_alt.clip(0, None) + dhi
    reflected = albedo * ghi * (1 - np.cos(b)) / 2
    return beam, diffuse, reflected, ghi


def panel_energy(tilt, surf_az, efficiency, area_m2, shading_loss=0.0, sky=SKY_FACTOR,
                 ambient=AMBIENT_C, system_loss=0.12, temp_coeff=-0.004, noct=45.0, step=0.25):
    """
    Monthly energy (kWh) and a typical-day power profile (kW) for each month.
    P = eta * A * G  (derated for cell temperature and system losses);  E = integral of P dt.
    """
    t = np.arange(0, 24, step) + step / 2
    monthly_kwh = np.zeros(12)
    profiles = np.zeros((12, len(t)))
    poa_daily = np.zeros(12)       # kWh/m^2/day on the panel plane
    ghi_daily = np.zeros(12)
    for m in range(12):
        beam, diff, refl, ghi = irradiance_components(MID_DAY[m], t, tilt, surf_az, sky[m])
        g = (beam * (1 - shading_loss) + diff * (1 - 0.5 * shading_loss) + refl)   # kW/m^2
        tcell = ambient[m] + (noct - 20.0) / 0.8 * g
        derate = (1 + temp_coeff * (tcell - 25.0)) * (1 - system_loss)
        p = efficiency * area_m2 * g * derate        # kW
        profiles[m] = p
        monthly_kwh[m] = p.sum() * step * DAYS_IN_MONTH[m]
        poa_daily[m] = g.sum() * step
        ghi_daily[m] = ghi.sum() * step
    return monthly_kwh, profiles, t, poa_daily, ghi_daily


def optimise(efficiency, area_m2, shading_loss, sky=SKY_FACTOR, ambient=AMBIENT_C):
    """Brute-force search of tilt (0-60) and azimuth (E to W) for maximum annual energy."""
    tilts = np.arange(0, 61, 2)
    azs = np.arange(-90, 91, 15)          # from south: -90 = East ... +90 = West
    grid = np.zeros((len(tilts), len(azs)))
    for i, tl in enumerate(tilts):
        for j, az in enumerate(azs):
            grid[i, j] = panel_energy(tl, az, efficiency, area_m2, shading_loss, sky, ambient, step=0.5)[0].sum()
    i, j = np.unravel_index(grid.argmax(), grid.shape)
    return tilts, azs, grid, tilts[i], azs[j]


def finances(monthly_kwh, monthly_usage, tariff, cost_per_kwp, kwp, export_rate=0.0,
             years=25, degradation=0.005, tariff_growth=0.03):
    """Self-consumption savings (+ optional export credit), payback and 25-year cash flow."""
    used = np.minimum(monthly_kwh, monthly_usage)
    exported = np.clip(monthly_kwh - monthly_usage, 0, None)
    saving_month = used * tariff + exported * export_rate
    annual = saving_month.sum()
    capex = kwp * cost_per_kwp
    cash, cum = [], -capex
    payback = None
    for y in range(1, years + 1):
        s = annual * (1 - degradation) ** (y - 1) * (1 + tariff_growth) ** (y - 1)
        cum += s
        cash.append(cum)
        if payback is None and cum >= 0:
            prev = cum - s
            payback = (y - 1) + (-prev / s)
    return dict(saving_month=saving_month, annual=annual, capex=capex, payback=payback,
                cash=np.array(cash), solar_fraction=used.sum() / max(monthly_usage.sum(), 1e-9))
