"""SolarSense - Physics-based rooftop solar optimiser for Chennai.  Run:  streamlit run app.py"""
import numpy as np, pandas as pd, streamlit as st
import physics as ph, plots

st.set_page_config(page_title="SolarSense", page_icon="☀️", layout="wide")
st.title("☀️ SolarSense")
st.caption("A physics-based rooftop solar energy & savings optimiser for Chennai (13.08° N, 80.27° E) "
           "| SRM Institute of Science and Technology - Department of Physics Mini Project")

# ---------------- Inputs ----------------
with st.sidebar:
    st.header("Your rooftop")
    roof = st.number_input("Roof area (m²)", 5.0, 1000.0, 40.0, 5.0)
    usable = st.slider("Usable fraction of roof (%)", 40, 90, 70,
                       help="Space left for walkways, water tanks and panel spacing") / 100
    tilt = st.slider("Panel tilt angle (°)", 0, 60, 13)
    bearing = st.slider("Panel direction (compass bearing °)", 0, 359, 180,
                        help="0 = North, 90 = East, 180 = South, 270 = West")
    shade = st.selectbox("Shading condition", list(ph.SHADING_LOSS.keys()))
    eff = st.slider("Panel efficiency (%)", 12.0, 24.0, 20.0, 0.5) / 100
    st.header("Electricity")
    tariff = st.number_input("Tariff (₹ / kWh)", 1.0, 20.0, 7.0, 0.5)
    usage_avg = st.number_input("Monthly usage (kWh)", 50.0, 10000.0, 400.0, 50.0)
    export_rate = st.number_input("Export credit for surplus (₹ / kWh)", 0.0, 10.0, 0.0, 0.5,
                                  help="0 = conservative: surplus units are not paid")
    cost_kwp = st.number_input("Installed cost (₹ / kWp)", 30000.0, 120000.0, 55000.0, 1000.0)
    with st.expander("Advanced: sky clearness by month"):
        sky = np.array([st.slider(m, 0.3, 1.0, float(v), 0.01, key=f"sky{m}")
                        for m, v in zip(ph.MONTHS, ph.SKY_FACTOR)])

surf_az = ((bearing - 180 + 180) % 360) - 180          # compass -> azimuth from south
area = roof * usable
kwp = eff * area * 1.0                                # STC irradiance = 1 kW/m²
loss = ph.SHADING_LOSS[shade]
usage = np.full(12, usage_avg)

@st.cache_data(show_spinner=False)
def run(tilt, surf_az, eff, area, loss, sky_t):
    return ph.panel_energy(tilt, surf_az, eff, area, loss, np.array(sky_t))

@st.cache_data(show_spinner="Searching all tilt/orientation combinations...")
def run_opt(eff, area, loss, sky_t):
    return ph.optimise(eff, area, loss, np.array(sky_t))

kwh, profiles, t, poa, ghi = run(tilt, surf_az, eff, area, loss, tuple(sky))
fin = ph.finances(kwh, usage, tariff, cost_kwp, kwp, export_rate)
tilts, azs, grid, best_tilt, best_az = run_opt(eff, area, loss, tuple(sky))
best_kwh = grid.max()
co2 = kwh.sum() * 0.71 / 1000                       # tonnes (India grid ~0.71 kg/kWh)

# ---------------- Results ----------------
c = st.columns(5)
c[0].metric("System size", f"{kwp:.1f} kWp")
c[1].metric("Avg daily generation", f"{kwh.sum()/365:.1f} kWh")
c[2].metric("Annual generation", f"{kwh.sum():,.0f} kWh")
c[3].metric("Annual savings", f"₹{fin['annual']:,.0f}")
c[4].metric("Payback period", f"{fin['payback']:.1f} yr" if fin["payback"] else "> 25 yr")
st.info(f"**Recommendation:** best fixed setting for Chennai is **{best_tilt}° tilt facing "
        f"{'South' if abs(best_az) < 8 else ('South-East' if best_az < 0 else 'South-West')}** "
        f"→ {best_kwh:,.0f} kWh/yr. Your setting gives {kwh.sum():,.0f} kWh/yr "
        f"({(kwh.sum()/best_kwh-1)*100:+.1f}% vs best). "
        f"It covers ~{fin['solar_fraction']*100:.0f}% of your usage and avoids ~{co2:.1f} t CO₂ per year.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Generation", "🕒 Daily profile", "🎯 Tilt optimiser",
                                          "💰 Savings", "📘 Physics & assumptions"])
with tab1:
    st.pyplot(plots.monthly_chart(kwh, usage))
    st.dataframe(pd.DataFrame({"Month": ph.MONTHS, "Irradiance on panel (kWh/m²/day)": poa.round(2),
                               "Generation (kWh)": kwh.round(0), "Savings (₹)": fin["saving_month"].round(0)}),
                 hide_index=True, use_container_width=True)
    st.download_button("⬇️ Download results (CSV)", pd.DataFrame({"month": ph.MONTHS, "kwh": kwh.round(1),
                       "savings_inr": fin["saving_month"].round(0)}).to_csv(index=False), "solarsense_results.csv")
with tab2:
    m = st.selectbox("Month", range(12), format_func=lambda i: ph.MONTHS[i], index=3)
    st.pyplot(plots.daily_profile_chart(t, profiles, m))
    st.pyplot(plots.sun_path_chart(ph.MID_DAY[m], tilt, surf_az, sky[m]))
    st.caption("The panel produces most power when the incidence angle θ is small (sun rays ⟂ panel).")
with tab3:
    st.pyplot(plots.heatmap_chart(tilts, azs, grid, best_tilt, best_az, tilt, max(-90, min(90, surf_az))))
    st.caption("Heat-map covers East-South-West orientations; a roof facing North is always worse in the northern hemisphere.")
with tab4:
    st.pyplot(plots.cashflow_chart(fin["cash"], fin["payback"]))
    st.write(f"Investment: **₹{fin['capex']:,.0f}** | 25-year net benefit: **₹{fin['cash'][-1]:,.0f}**")
with tab5:
    st.markdown(r"""
**Physics used**
1. Solar declination: $\delta = 23.45^\circ \sin\!\big[\tfrac{360}{365}(284+n)\big]$
2. Hour angle: $\omega = 15^\circ (t_{solar}-12)$
3. Sun altitude: $\sin\alpha = \sin\phi\sin\delta + \cos\phi\cos\delta\cos\omega$
4. Angle of incidence on a tilted panel (tilt β, azimuth γ):
   $\cos\theta = \sin\delta\sin\phi\cos\beta - \sin\delta\cos\phi\sin\beta\cos\gamma + \cos\delta\cos\phi\cos\beta\cos\omega + \cos\delta\sin\phi\sin\beta\cos\gamma\cos\omega + \cos\delta\sin\beta\sin\gamma\sin\omega$
5. Beam irradiance: $I_b = I_{DN}\cos\theta$, with $I_{DN} = 1.353\,(0.7)^{AM^{0.678}}$ and air-mass $AM = 1/\sin\alpha$ (Meinel model)
6. Total on panel: $G = I_b + I_d\frac{1+\cos\beta}{2} + \rho\, I_{GH}\frac{1-\cos\beta}{2}$
7. Power: $P = \eta\, A\, G$ (derated for temperature) and Energy: $E = \int P\,dt$
8. Cell temperature: $T_c = T_{amb} + \frac{NOCT-20}{0.8}G$; power falls ~0.4 % per °C above 25 °C

**Assumptions (be honest about limits)**
- Typical-day (mid-month) calculation; clear-sky model scaled by an assumed monthly sky-clearness factor for Chennai.
- Diffuse light = 10 % of beam; ground albedo 0.2; 12 % system losses (inverter, wiring, dust).
- Shading is a simple percentage loss; electricity tariff is a flat average (real slab tariffs differ).
- Cost, tariff growth (3 %/yr) and panel degradation (0.5 %/yr) are editable estimates, not quotations.
""")
