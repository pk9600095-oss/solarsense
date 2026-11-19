import numpy as np, physics as ph, plots, os
os.makedirs("figs", exist_ok=True)
roof, usable, eff, tilt, az = 40, .7, .20, 13, 0
area = roof*usable
kwh, prof, t, poa, ghi = ph.panel_energy(tilt, az, eff, area)
usage = np.full(12, 400.)
fin = ph.finances(kwh, usage, 7.0, 55000, eff*area)
tilts, azs, grid, bt, ba = ph.optimise(eff, area, 0)
plots.monthly_chart(kwh, usage).savefig("figs/monthly.png", dpi=150)
plots.daily_profile_chart(t, prof, 3).savefig("figs/daily.png", dpi=150)
plots.heatmap_chart(tilts, azs, grid, bt, ba, tilt, az).savefig("figs/heatmap.png", dpi=150)
plots.cashflow_chart(fin["cash"], fin["payback"]).savefig("figs/cashflow.png", dpi=150)
plots.sun_path_chart(105, tilt, az, .82).savefig("figs/sunpath.png", dpi=150)
print("kWp", eff*area, "annual", kwh.sum().round(), "best", bt, ba, "savings", fin["annual"].round(), "payback", fin["payback"], "net25", fin["cash"][-1].round())
