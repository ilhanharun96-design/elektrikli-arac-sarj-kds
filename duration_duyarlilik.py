# -*- coding: utf-8 -*-
"""Duration ile Start/End bağlantı aralığı varsayımlarını karşılaştırır.

Bu betik ana veri/model dosyalarını değiştirmez. Yalnızca
outputs_load_profile/duration_duyarlilik/ altına karşılaştırma çıktıları yazar.
"""
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "data" / "ChargingRecords.csv"
OUT = BASE / "outputs_load_profile" / "duration_duyarlilik"
OUT.mkdir(parents=True, exist_ok=True)

START_ANALYSIS = pd.Timestamp("2021-10-07 00:00:00")
END_ANALYSIS = pd.Timestamp("2022-09-01 00:00:00")
SCENARIOS = {"U100": 1.0, "F50": 0.5, "F25": 0.25}


def allocate_energy(starts_h, durations_h, energies, n_hours):
    """Enerjiyi oturum aralığının saatlerle kesişimine orantılı dağıtır."""
    result = np.zeros(n_hours, dtype=float)
    for start, duration, energy in zip(starts_h, durations_h, energies):
        if not np.isfinite(start + duration + energy) or duration <= 0:
            continue
        end = start + duration
        first = max(0, int(np.floor(start)))
        last = min(n_hours - 1, int(np.ceil(end) - 1))
        if last < first:
            continue
        rate = energy / duration
        for hour in range(first, last + 1):
            overlap = max(0.0, min(end, hour + 1) - max(start, hour))
            result[hour] += rate * overlap
    return result


def main():
    if not DATA.exists():
        raise FileNotFoundError(f"Ham veri bulunamadı: {DATA}")
    df = pd.read_csv(DATA)
    required = ["StartDay", "StartTime", "EndDay", "EndTime", "Duration", "Demand"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Eksik sütunlar: {missing}")

    raw_n = len(df)
    df = df.drop_duplicates().copy()
    df["Duration"] = pd.to_numeric(df["Duration"], errors="coerce")
    df["Demand"] = pd.to_numeric(df["Demand"], errors="coerce")
    df["start"] = pd.to_datetime(
        df["StartDay"].astype(str).str.strip() + " " + df["StartTime"].astype(str).str.strip(),
        errors="coerce",
    )
    df["end"] = pd.to_datetime(
        df["EndDay"].astype(str).str.strip() + " " + df["EndTime"].astype(str).str.strip(),
        errors="coerce",
    )
    df["connection_minutes"] = (df["end"] - df["start"]).dt.total_seconds() / 60

    valid_fields = df[["start", "end", "Duration", "Demand"]].notna().all(axis=1)
    excluded = (
        ~valid_fields
        | (df["Duration"] <= 0)
        | (df["connection_minutes"] <= 0)
        | ((df["Duration"] - df["connection_minutes"]) > 5)
    )
    valid = df.loc[~excluded].copy()
    valid = valid[(valid["start"] >= START_ANALYSIS) & (valid["start"] < END_ANALYSIS)].copy()
    if valid.empty:
        raise ValueError("Analiz döneminde geçerli oturum bulunamadı.")

    valid["duration_difference_min"] = valid["Duration"] - valid["connection_minutes"]
    short = valid["duration_difference_min"] < -5

    start_grid = valid["start"].min().floor("h")
    starts_h = ((valid["start"] - start_grid).dt.total_seconds() / 3600).to_numpy()
    energy = valid["Demand"].to_numpy(dtype=float)

    summary_rows = []

    duration_options = {
        "Duration_kaynak": valid["Duration"].to_numpy(dtype=float) / 60,
        "Baglanti_araligi": valid["connection_minutes"].to_numpy(dtype=float) / 60,
    }
    max_end_h = max(float(np.max(starts_h + d * max(SCENARIOS.values()))) for d in duration_options.values())
    n_hours = int(np.ceil(max_end_h)) + 1
    index = pd.date_range(start_grid, periods=n_hours, freq="h")
    analysis_mask = index < END_ANALYSIS
    hourly = pd.DataFrame(index=index)
    hourly.index.name = "datetime"

    for duration_name, duration_hours in duration_options.items():
        for scenario, fraction in SCENARIOS.items():
            values = allocate_energy(starts_h, duration_hours * fraction, energy, len(index))
            analysis_values = values[analysis_mask]
            col = f"{duration_name}_{scenario}_kWh_saat"
            hourly[col] = values
            summary_rows.append({
                "sure_varsayimi": duration_name,
                "senaryo": scenario,
                "oturum_sayisi": len(valid),
                "toplam_enerji_kWh": float(energy.sum()),
                "profil_toplam_kWh": float(values.sum()),
                "enerji_korunum_farki_kWh": float(values.sum() - energy.sum()),
                "analiz_donemi_ortalama_kWh_saat": float(analysis_values.mean()),
                "analiz_donemi_medyan_kWh_saat": float(np.median(analysis_values)),
                "analiz_donemi_p95_kWh_saat": float(np.quantile(analysis_values, .95)),
                "analiz_donemi_p99_kWh_saat": float(np.quantile(analysis_values, .99)),
                "analiz_donemi_maksimum_kWh_saat": float(analysis_values.max()),
                "analiz_donemi_maksimum_saati": str(index[np.flatnonzero(analysis_mask)[int(analysis_values.argmax())]]),
            })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "sure_varsayimi_karsilastirmasi.csv", index=False, encoding="utf-8-sig")
    hourly.to_csv(OUT / "saatlik_profiller.csv", encoding="utf-8-sig")

    diagnostics = pd.DataFrame([{
        "ham_satir": raw_n,
        "tekrarsiz_satir": len(df),
        "analiz_oturumu": len(valid),
        "Duration_baglantidan_5dk_kisa_oturum": int(short.sum()),
        "kisa_oturum_enerjisi_kWh": float(valid.loc[short, "Demand"].sum()),
        "kisa_oturum_medyan_fark_dk": float((-valid.loc[short, "duration_difference_min"]).median()) if short.any() else 0.0,
        "kisa_oturum_medyan_Duration_baglanti_orani": float((valid.loc[short, "Duration"] / valid.loc[short, "connection_minutes"]).median()) if short.any() else np.nan,
        "analiz_baslangici": str(index[analysis_mask].min()),
        "analiz_son_saati": str(index[analysis_mask].max()),
        "profil_izgarasi_son_saati": str(index.max()),
    }])
    diagnostics.to_csv(OUT / "sure_tutarsizligi_tanisi.csv", index=False, encoding="utf-8-sig")

    lines = [
        "DURATION / BAĞLANTI ARALIĞI DUYARLILIK ANALİZİ",
        "",
        "Duration, kaynak makalenin veri sözlüğünde şarj cihazına bağlantı süresi (dakika) olarak tanımlanır.",
        "Bu değişken aktif enerji aktarım süresi veya ölçülmüş güç profili değildir.",
        "Bu nedenle iki süre tanımıyla da enerji eşit güç varsayımı altında saatlere dağıtılmıştır.",
        "U100/F50/F25 gerçek ölçüm değil, süre varsayımına dayalı duyarlılık senaryolarıdır.",
        "",
        f"Ham satır: {raw_n}",
        f"Tekrarsız satır: {len(df)}",
        f"Analiz oturumu: {len(valid)}",
        f"Duration bağlantı aralığından 5 dakikadan fazla kısa oturum: {int(short.sum())}",
        f"Bu kısa oturumların enerjisi: {valid.loc[short, 'Demand'].sum():.2f} kWh",
        "",
        summary.round(3).to_string(index=False),
        "",
        "Enerji korunumu tüm oturumların bitişini kapsayan genişletilmiş saat ızgarasında kontrol edilir.",
        "Özet profil istatistikleri yalnızca 2022-09-01 öncesindeki analiz saatlerinde hesaplanır.",
        "Sonuçlar gerçek şebeke yükü veya anlık şarj gücü olarak yorumlanmamalıdır.",
    ]
    (OUT / "analiz_notu.txt").write_text("\n".join(lines), encoding="utf-8")
    print("Duyarlılık analizi tamamlandı:", OUT)
    print(summary.round(3).to_string(index=False))
    print("Kısa Duration oturumu:", int(short.sum()), "| enerji:", round(valid.loc[short, "Demand"].sum(), 2))


if __name__ == "__main__":
    main()
