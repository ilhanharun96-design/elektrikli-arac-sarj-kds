# -*- coding: utf-8 -*-
"""Rolling-origin doğrulama çıktılarından uygulama performans özetini üretir.

R1_B0_arti_artik_HGB bilerek dışarıda bırakılır: mevcut eski deneyde R1 eğitim
artıkları, aynı eğitim kümesinden hesaplanan in-sample B0 tahminleriyle üretilmiştir.
Bu nedenle R1, diğer yöntemlerle eş koşullu ve adil bir karşılaştırma değildir.
"""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
OUT = BASE / "outputs_modeling"
ABLATION = OUT / "iyilestirme_denemeleri" / "rolling_ablasyon_sonuclari.csv"
VARIANTS = BASE / "archive" / "experiment_outputs" / "modeling" / "referans_ve_artik_denemeleri" / "sonuclar.csv"
DEST = OUT / "rolling_origin_karsilastirma.csv"


def mean_metrics(df, target, method):
    part = df[(df.hedef == target) & (df.yontem == method)]
    if part.empty:
        raise ValueError(f"Eksik yöntem/target: {method} / {target}")
    return part[["MAE", "WAPE"]].mean()


def main():
    a = pd.read_csv(ABLATION)
    v = pd.read_csv(VARIANTS)
    targets = {
        "session_start_count": "oturum",
        "started_session_energy_kwh": "enerji",
    }
    methods = [
        ("B0_profil_x_seviye", "B0 Profil × Seviye", "Ana istatistiksel yöntem", "variants"),
        ("B1_seviye_168_24_karisim", "B1 Seviye karışımı", "B0 varyantı", "variants"),
        ("B2_son8hafta_profil", "B2 Son 8 hafta profili", "B0 varyantı", "variants"),
        ("B3_son8hafta_ve_karisim", "B3 Profil ve seviye karışımı", "B0 varyantı", "variants"),
        ("E2_oran_hedef_agirlikli", "E2 Oran hedefli HGB", "Makine öğrenmesi", "ablation"),
        ("E1_takvim_indeksi_cikarildi", "E1 Takvim indeksleri çıkarılmış HGB", "Makine öğrenmesi", "ablation"),
        ("BASE_profil_statik", "Statik profil", "Referans yöntem", "ablation"),
        ("REF_45_ozellik", "İlk HGB (45 özellik)", "İlk referans model", "ablation"),
    ]
    rows = []
    for code, display, group, source in methods:
        row = {"yontem_kodu": code, "Yöntem": display, "Sınıf": group}
        for target, prefix in targets.items():
            src = v if source == "variants" else a
            m = mean_metrics(src, target, code)
            row[f"{prefix}_MAE"] = float(m.MAE)
            row[f"{prefix}_WAPE_pct"] = float(m.WAPE)
        rows.append(row)
    result = pd.DataFrame(rows)
    result.to_csv(DEST, index=False, encoding="utf-8-sig")
    print("Oluşturuldu:", DEST)
    print(result.round(4).to_string(index=False))
    print("Not: R1 eski in-sample artık üretimi nedeniyle karşılaştırmaya alınmadı.")


if __name__ == "__main__":
    main()
