# -*- coding: utf-8 -*-
"""S1 q=0.90 kapsamasını tahmin ufkuna göre tanılar.

Aynı B0/S1 tanımı korunur; Haziran-Ağustos rolling-origin kıvrımları kullanılır.
Test dönemi Eylül 2022'ye dokunulmaz.
"""
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
FE = BASE / "outputs_feature_engineering"
OUT = BASE / "outputs_modeling" / "belirsizlik_ufuk_tanisi"
OUT.mkdir(parents=True, exist_ok=True)
TARGETS = ["session_start_count", "started_session_energy_kwh"]
FOLDS = [("2022-06-01", "2022-07-01"), ("2022-07-01", "2022-08-01"), ("2022-08-01", "2022-09-01")]
CAL_WEEKS = 8
Q = .90


def b0(train, evaluation, target):
    unique = train.drop_duplicates("target_datetime")
    profile = unique.groupby(["target_weekday", "target_hour"])[target].mean()
    overall = float(unique[target].mean())
    keys = pd.MultiIndex.from_arrays([evaluation.target_weekday.astype(int), evaluation.target_hour.astype(int)])
    profile_values = profile.reindex(keys).to_numpy(dtype=float)
    level = evaluation[f"{target}_rolling_mean_168"].to_numpy(dtype=float)
    return np.maximum(profile_values / overall * level, 0)


def main():
    train = pd.read_csv(FE / "train_verisi.csv", parse_dates=["origin_datetime", "target_datetime"])
    val = pd.read_csv(FE / "validation_verisi.csv", parse_dates=["origin_datetime", "target_datetime"])
    data = pd.concat([train, val], ignore_index=True)
    if data.target_datetime.max() >= pd.Timestamp("2022-09-01"):
        raise ValueError("Eylül test verisi kalibrasyon verisine karışmış.")
    rows = []
    for target in TARGETS:
        for start, end in FOLDS:
            start, end = pd.Timestamp(start), pd.Timestamp(end)
            cal_start = start - pd.Timedelta(weeks=CAL_WEEKS)
            prior = data[data.target_datetime < cal_start]
            cal = data[(data.target_datetime >= cal_start) & (data.target_datetime < start)]
            fit = data[data.target_datetime < start]
            ev = data[(data.target_datetime >= start) & (data.target_datetime < end)]
            cal_pred = b0(prior, cal, target)
            actual_cal = cal[target].to_numpy(dtype=float)
            m = float(actual_cal.mean())
            scale_cal = np.sqrt(np.maximum(cal_pred + .05*m, 1e-9))
            zq = float(np.quantile((actual_cal-cal_pred)/scale_cal, Q))
            ev_pred = b0(fit, ev, target)
            scale_ev = np.sqrt(np.maximum(ev_pred + .05*m, 1e-9))
            upper = np.maximum(ev_pred + zq*scale_ev, 0)
            ev = ev.copy()
            ev["actual"] = ev[target].to_numpy(dtype=float)
            ev["b0"] = ev_pred
            ev["s1"] = upper
            ev["covered"] = ev.actual <= ev.s1
            for horizon, g in ev.groupby("forecast_horizon"):
                rows.append({
                    "hedef": target,
                    "fold": start.strftime("%Y-%m"),
                    "forecast_horizon": int(horizon),
                    "tahmin_hata_satiri": len(g),
                    "benzersiz_hedef_saati": int(g.target_datetime.nunique()),
                    "q": Q,
                    "kapsama": float(g.covered.mean()),
                    "ortalama_b0": float(g.b0.mean()),
                    "ortalama_s1_genisligi": float((g.s1-g.b0).mean()),
                    "z_q": zq,
                })
    detail = pd.DataFrame(rows)
    detail.to_csv(OUT / "ufka_gore_s1_kapsama.csv", index=False, encoding="utf-8-sig")
    avg = detail.groupby(["hedef", "forecast_horizon"])[["kapsama", "ortalama_s1_genisligi"]].mean().reset_index()
    avg.to_csv(OUT / "ufka_gore_s1_ortalama.csv", index=False, encoding="utf-8-sig")
    print("UFKA GÖRE S1 KAPSAMASI (üç fold ortalaması)")
    for target, group in avg.groupby("hedef"):
        print("\n", target)
        print(group.round(3).to_string(index=False))
        print("min/max coverage:", round(group.kapsama.min(),3), round(group.kapsama.max(),3))


if __name__ == "__main__":
    main()
