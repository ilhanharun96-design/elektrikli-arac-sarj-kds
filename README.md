# Elektrikli Araç Şarj Talebi – Karar Destek Sistemi

Bu klasör, elektrikli araç şarj oturumlarından saatlik talep tahmini ve varsayımsal yaklaşık yük senaryoları üreten bir karar destek prototipidir.

## Hızlı başlangıç

**Gereksinim:** Python 3.11–3.13

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Uygulama 01.09.2022 için tarihsel 24 saatlik örnek tahmin üretir. Canlı veriyle çalışmaz.

## Uygulama sekmeleri

1. Oturum başlangıç tahmini
2. Başlangıç saatine atfedilen enerji tahmini
3. Yaklaşık saatlik yük tahmini (U100/F50/F25)
4. Model performansı
5. Talep yoğunluğu analizi

## Baştan veri işleme sırası

Ham veri dosyası `data/ChargingRecords.csv` konumundadır. Orijinal dosya değiştirilmez.

```powershell
python data_validation.py
python data_cleaning.py
python eda_analysis.py
python feature_engineering.py
python yaklasik_yuk_profili.py
```

HGB referans modelini yeniden eğitmek isterseniz ayrıca:

```powershell
python model_training.py
```

Ek doğrulama/duyarlılık betikleri:

```powershell
python duration_duyarlilik.py
python yuk_seviye_duyarlilik.py
python belirsizlik_ufuk_tanisi.py
python performans_ozeti_olustur.py
```

`performans_ozeti_olustur.py`, arşivde saklanan rolling-origin deney sonuçlarını kullanarak arayüzün performans tablosunu üretir.

## Önemli metodolojik sınırlar

- B0, makine öğrenmesi algoritması değil, istatistiksel profil × seviye yöntemidir. HGB karşılaştırma modelidir.
- `started_session_energy_kwh`, oturum başlangıç saatine atfedilen enerjidir; gerçek saatlik şebeke tüketimi değildir.
- Kaynak veri sözlüğündeki `Duration`, bağlantı süresidir; aktif enerji aktarım süresi değildir.
- U100/F50/F25 eşit güç dağılımı varsayımına dayalı duyarlılık senaryolarıdır; ölçülmüş güç profili değildir.
- Sistem gerçek zamanlı şebeke kontrolü veya araç bazında akıllı şarj optimizasyonu yapmaz.
- Eylül 2022 ilk HGB referans modelinin değerlendirmesinde kullanıldığı için bütün proje için tamamen bağımsız test dönemi değildir.

Ayrıntılı yöntem, sayısal sonuçlar, sınırlamalar ve dosya durumu için `DURUM.md` dosyasına bakın. Güncellenmiş akademik rapor `docs/Elektrikli_Arac_Sarj_KDS_Nihai_Rapor_Guncel.docx` konumundadır; yapılan rapor değişiklikleri `docs/RAPOR_GUNCELLEME_NOTLARI.md` dosyasında özetlenmiştir.

## Klasör düzeni

- `app.py`: Beş sekmeli ana Streamlit uygulaması
- `data/`: Orijinal ham veri
- `outputs_cleaning/`: Temizlenmiş ve saatlik hedef verileri
- `outputs_feature_engineering/`: Eğitim, doğrulama ve test tabloları
- `outputs_modeling/`: Model karşılaştırma ve doğrulama sonuçları
- `outputs_load_profile/`: Yaklaşık yük profilleri ve duyarlılık analizleri
- `archive/`: Eski arayüzler, deney betikleri ve tarihsel notlar

## Kaynak veri

Baek, K., Lee, E., & Kim, J. (2024). *A dataset for multi-faceted analysis of electric vehicle charging transactions*. Scientific Data, 11, Article 262. https://doi.org/10.1038/s41597-024-02942-9
