# -*- coding: utf-8 -*-
"""Yaklaşık yük tahmininde seviye serisi seçimini rolling-origin ile karşılaştırır.

Karşılaştırma:
- mevcut: yük profilinin şekli × başlangıç enerjisi serisinin son 168 saat seviyesi
- alternatif: yük profilinin şekli × aynı yük serisinin son 168 saat seviyesi

Her satırın seviye değeri origin_datetime anında bilinen son 168 saatten hesaplanır.
Eylül 2022 test dönemi kullanılmaz.
"""
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
FE = BASE / "outputs_feature_engineering"
LP = BASE / "outputs_load_profile" / "saatlik_yaklasik_yuk.csv"
OUT = BASE / "outputs_load_profile" / "yuk_seviye_duyarlilik"
OUT.mkdir(parents=True, exist_ok=True)

TEST_START = pd.Timestamp("2022-09-01")
PROFILE_START = pd.Timestamp("2021-10-07 18:00")
SCENARIOS = {"U100": "yuk_U100_kwh", "F50": "yuk_F50_kwh", "F25": "yuk_F25_kwh"}
FOLDS = [("2022-06-01", "2022-07-01"), ("2022-07-01", "2022-08-01"), ("2022-08-01", "2022-09-01")]
CAL_WEEKS = 8
BUFFER = pd.Timedelta(days=2)
Q = 0.90


def load_data():
    cols = ["origin_datetime", "target_datetime", "forecast_horizon", "target_weekday", "target_hour",
            "started_session_energy_kwh", "started_session_energy_kwh_rolling_mean_168"]
    tr = pd.read_csv(FE / "train_verisi.csv", usecols=cols, parse_dates=["origin_datetime", "target_datetime"])
    va = pd.read_csv(FE / "validation_verisi.csv", usecols=cols, parse_dates=["origin_datetime", "target_datetime"])
    data = pd.concat([tr, va], ignore_index=True)
    if data.target_datetime.max() >= TEST_START:
        raise ValueError("Eylül 2022 test dönemi eğitim/kalibrasyon verisine karışmış.")
    load = pd.read_csv(LP, parse_dates=["datetime"]).set_index("datetime").sort_index()
    return data, load


def profile_factor(series, evaluation, cutoff):
    hist = series[(series.index >= PROFILE_START) & (series.index < cutoff)]
    if hist.empty:
        raise ValueError(f"{cutoff} öncesinde profil geçmişi yok.")
    frame = pd.DataFrame({"v": hist.to_numpy(), "wd": hist.index.dayofweek, "hr": hist.index.hour})
    prof = frame.groupby(["wd", "hr"]).v.mean()
    keys = pd.MultiIndex.from_arrays([evaluation.target_weekday.astype(int), evaluation.target_hour.astype(int)])
    factor = prof.reindex(keys).to_numpy(dtype=float) / float(hist.mean())
    if not np.isfinite(factor).all():
        raise ValueError("Profil katsayısında eksik değer var.")
    return factor


def level_at_origin(series, evaluation):
    rolling = series.rolling(168, min_periods=168).mean()
    levels = rolling.reindex(pd.DatetimeIndex(evaluation.origin_datetime)).to_numpy(dtype=float)
    if not np.isfinite(levels).all():
        raise ValueError("Origin zamanında son 168 saatlik yük seviyesi hesaplanamadı.")
    return levels


def metrics(actual, pred, horizons):
    pred = np.maximum(np.asarray(pred, dtype=float), 0)
    actual = np.asarray(actual, dtype=float)
    h24 = np.asarray(horizons) == 24
    ga = actual[h24] >= np.quantile(actual[h24], .90)
    gp = pred[h24] >= np.quantile(pred[h24], .90)
    return {
        "MAE": float(np.mean(np.abs(actual - pred))),
        "WAPE_pct": float(np.sum(np.abs(actual - pred)) / np.sum(actual) * 100),
        "bias": float(np.mean(actual - pred)),
        "MAE_h24": float(np.mean(np.abs(actual[h24] - pred[h24]))),
        "zirve_recall_h24": float(np.sum(ga & gp) / max(int(ga.sum()), 1)),
    }


def main():
    data, load = load_data()
    rows, calibration_rows = [], []
    for scenario, col in SCENARIOS.items():
        series = load[col].dropna()
        for start, end in FOLDS:
            start, end = pd.Timestamp(start), pd.Timestamp(end)
            cutoff = start - BUFFER
            cal_start = cutoff - pd.Timedelta(weeks=CAL_WEEKS)
            evaluation = data[(data.target_datetime >= start) & (data.target_datetime < end)].copy()
            calibration = data[(data.target_datetime >= cal_start) & (data.target_datetime < cutoff)].copy()
            actual_eval = series.reindex(pd.DatetimeIndex(evaluation.target_datetime)).to_numpy(dtype=float)
            actual_cal = series.reindex(pd.DatetimeIndex(calibration.target_datetime)).to_numpy(dtype=float)
            if not np.isfinite(actual_eval).all() or not np.isfinite(actual_cal).all():
                raise ValueError(f"{scenario}/{start:%Y-%m}: hedef yük serisinde eksik saat.")

            fac_eval = profile_factor(series, evaluation, cutoff)
            fac_cal = profile_factor(series, calibration, cal_start)

            current_level_eval = evaluation["started_session_energy_kwh_rolling_mean_168"].to_numpy(dtype=float)
            current_level_cal = calibration["started_session_energy_kwh_rolling_mean_168"].to_numpy(dtype=float)
            load_level_eval = level_at_origin(series, evaluation)
            load_level_cal = level_at_origin(series, calibration)

            predictions = {
                "mevcut_baslangic_enerjisi_seviyesi": fac_eval * current_level_eval,
                "alternatif_yuk_serisi_seviyesi": fac_eval * load_level_eval,
            }
            for method, pred in predictions.items():
                row = {"senaryo": scenario, "fold": start.strftime("%Y-%m"), "yontem": method}
                row.update(metrics(actual_eval, pred, evaluation.forecast_horizon.to_numpy()))
                rows.append(row)

                if method == "mevcut_baslangic_enerjisi_seviyesi":
                    cal_pred = fac_cal * current_level_cal
                else:
                    cal_pred = fac_cal * load_level_cal
                m = float(np.mean(actual_cal))
                scale_cal = np.sqrt(np.maximum(cal_pred + .05 * m, 1e-9))
                zq = float(np.quantile((actual_cal - cal_pred) / scale_cal, Q))
                pred = np.maximum(pred, 0)
                scale_eval = np.sqrt(np.maximum(pred + .05 * m, 1e-9))
                upper = np.maximum(pred + zq * scale_eval, 0)
                h24 = evaluation.forecast_horizon.to_numpy() == 24
                calibration_rows.append({
                    "senaryo": scenario, "fold": start.strftime("%Y-%m"), "yontem": method,
                    "q": Q, "kapsama": float(np.mean(actual_eval <= upper)),
                    "kapsama_h24": float(np.mean(actual_eval[h24] <= upper[h24])),
                    "ortalama_genislik": float(np.mean(upper - pred)),
                    "z_kalibrasyon": zq,
                    "kalibrasyon_satiri": len(calibration),
                })

    score = pd.DataFrame(rows)
    bands = pd.DataFrame(calibration_rows)
    score.to_csv(OUT / "seviye_model_karsilastirmasi.csv", index=False, encoding="utf-8-sig")
    bands.to_csv(OUT / "s1_kapsama_karsilastirmasi.csv", index=False, encoding="utf-8-sig")

    summary = score.groupby(["senaryo", "yontem"])[["MAE", "WAPE_pct", "bias", "MAE_h24", "zirve_recall_h24"]].mean().reset_index()
    band_summary = bands.groupby(["senaryo", "yontem"])[["kapsama", "kapsama_h24", "ortalama_genislik"]].mean().reset_index()
    summary.to_csv(OUT / "seviye_ortalama_ozet.csv", index=False, encoding="utf-8-sig")
    band_summary.to_csv(OUT / "s1_ortalama_ozet.csv", index=False, encoding="utf-8-sig")
    print("MODEL KARŞILAŞTIRMASI")
    print(summary.round(4).to_string(index=False))
    print("\nS1 KAPSAMA KARŞILAŞTIRMASI")
    print(band_summary.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
