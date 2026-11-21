# Proje Durum Dosyası

**Son güncelleme:** 21.11.2026  
**Ana uygulama:** `app.py`  
**Proje türü:** Tarihsel veriyle çalışan, 24 saatlik tahmin ve senaryo tabanlı karar destek prototipi

## 1. Projenin amacı ve kapsamı

Elektrikli araç şarj oturumlarından hareketle:

1. Gelecek 24 saat için saatlik oturum başlangıç sayısını tahmin etmek,
2. Oturum başlangıç saatine atfedilen toplam enerjiyi tahmin etmek,
3. U100, F50 ve F25 varsayımlarıyla yaklaşık saatlik enerji/yük dağılımını incelemek,
4. B0 noktasal tahmininin yanında S1 ihtiyatlı üst tahmin göstergesini sunmak,
5. Sonuçları beş sekmeli Streamlit karar destek arayüzünde göstermek.

**Karar verici:** Şarj ağı operasyon yöneticisi veya enerji yöneticisi.

**Sistem sınırı:** Uygulama 01.09.2022 için tarihsel bir tahmin örneği üretir. Canlı veri akışı, gerçek zamanlı şebeke kontrolü, araç bazında güç tahsisi veya tamamlanmış optimizasyon motoru içermez.

## 2. Değişmez veri ve yorumlama kuralları

- `data/ChargingRecords.csv` ham veri dosyasıdır; analiz betikleri bu dosyayı değiştirmez.
- Kaynak veri sözlüğünde `Duration`, aracın şarj cihazına bağlı kaldığı süredir (dakika); aktif enerji aktarım süresi veya ölçülmüş güç profili değildir.
- `Demand`, oturum boyunca araca aktarılan enerji miktarıdır (kWh).
- `Demand / Duration` ancak enerjinin bağlantı süresine eşit güçle dağıtıldığı varsayımı altında türetilen ortalama güç göstergesidir. Ölçülmüş anlık güç değildir.
- `started_session_energy_kwh`, oturumun başladığı saate atfedilen oturum enerjisidir; o saatte gerçekten tüketilmiş saatlik şebeke enerjisi değildir.
- U100/F50/F25 gerçek sayaç profilleri değil, enerjinin bağlantı süresinin tamamına veya ilk belirli kesrine eşit güçle dağıtıldığı varsayımsal duyarlılık senaryolarıdır.
- Gerçek sayaç gücü, istasyon/trafo kapasitesi ve fiziksel şebeke kısıtları bulunmadığından kapasite güvenliği veya otomatik güç optimizasyonu iddia edilmez.
- `ChargerType` değerleri bu çalışmada AC/DC türü olarak yorumlanmaz; kaynak makalede bu alan şarj hızı kategorisidir. AC/DC bilgisi ayrı `ChargerACDC` sütununda tanımlıdır ancak çalışma CSV'sinde bulunmamaktadır.
- Eylül 2022 ilk HGB referans modelinin test değerlendirmesinde kullanılmıştır. Bu nedenle bütün proje açısından tamamen hiç görülmemiş bağımsız test dönemi olarak tanımlanmaz. B0/S1 nihai uygulama tahmini Eylül gözlemlerini kullanmaz.

## 3. Veri hazırlama durumu

| Kontrol | Sonuç |
|---|---:|
| Ham kayıt | 72.856 |
| Tam yinelenen kayıt | 13 |
| Tekrarsız oturum | 72.843 |
| Yaklaşık yük analizine uygun oturum | 72.039 |
| Yaklaşık yük analizinden dışlanan oturum | 804 |
| Dışlanan oturumların enerjisi | 5.034,10 kWh |
| Saatlik seri uzunluğu | 8.767 saat |

Dışlama kuralları: negatif Duration (17), sıfır Duration (718), Duration'ın bağlantı aralığından 5 dakikadan fazla uzun olması (69) ve bağlantı aralığının sıfır veya negatif olması (47). Birden fazla koşula uyan kayıtlar birleşimde yalnızca bir kez sayılır. Bu 804 kayıt oturum sayısı ve başlangıç enerjisi hedeflerinden değil, yaklaşık yük analizinden çıkarılır.

Özellik mühendisliği çıktıları:

- 45 model özelliği,
- 24 saatlik doğrudan çok adımlı tahmin veri yapısı,
- Eğitim: 07.10.2021–31.07.2022,
- Doğrulama: Ağustos 2022,
- İlk HGB değerlendirme/test dönemi: Eylül 2022.

## 4. Tahmin yöntemleri ve doğrulama

### 4.1. Ana yöntem: B0 Profil × Seviye

B0, makine öğrenmesi algoritması değil, istatistiksel profil-seviye tahmin yöntemidir:

`B0 = (geçmiş hafta-gün-saat ortalama profili / profil genel ortalaması) × son 168 saatlik seviye`

Haziran, Temmuz ve Ağustos 2022 rolling-origin doğrulamasında ortalama MAE:

| Yöntem | Oturum MAE | Başlangıç enerjisi MAE |
|---|---:|---:|
| B0 Profil × Seviye | **2,5632** | **55,0065 kWh** |
| B1 seviye karışımı | 2,5719 | 55,1695 kWh |
| B2 son 8 hafta profili | 2,5646 | 56,0030 kWh |
| B3 profil ve seviye karışımı | 2,5760 | 56,0680 kWh |
| E2 oran hedefli HGB | 2,8440 | 60,4289 kWh |
| E1 takvim indeksleri çıkarılmış HGB | 2,8716 | 61,1026 kWh |
| Statik profil | 3,1939 | 64,1546 kWh |
| İlk 45 özellikli HGB referansı | 3,2526 | 71,4464 kWh |

B0 iki hedefte de en düşük ortalama MAE'yi verdiği için ana noktasal tahmin yöntemi olarak seçilmiştir. B0 ile B2 arasındaki oturum MAE farkı çok küçüktür; B0'ın açık ara üstün olduğu iddia edilmez.

**R1 hakkında metodolojik not:** Eski R1 artık-öğrenen deneyinde eğitim artıkları, aynı eğitim kümesinde oluşturulan in-sample B0 tahminlerinden hesaplanmıştır. Bu nedenle diğer yöntemlerle eş koşullu bir karşılaştırma değildir ve nihai performans tablosundan çıkarılmıştır. Eski betik ve çıktısı `archive/` altında saklanır; geçerli nihai yöntem olarak kullanılmaz.

### 4.2. İlk HGB referans modelinin Eylül değerlendirmesi

| Hedef | MAE | WAPE |
|---|---:|---:|
| Oturum başlangıç sayısı | 2,9489 | %34,03 |
| Başlangıç enerjisi | 61,5374 kWh | %39,88 |

Bu sonuç rolling-origin karşılaştırmasından ayrı bir deneydir. Eylül dönemi ilk HGB değerlendirmesinde kullanıldığı için bağımsız test sınırlaması açıkça belirtilmelidir.

## 5. S1 belirsizlik üst sınırı

- Ana noktasal tahmin B0'dır.
- S1, son 8 haftalık kalibrasyon dönemindeki standartlaştırılmış artıkların `q=0,90` kantiline dayanır.
- Ölçekleme karekök yaklaşımıdır.
- Kalibrasyon tablosundaki 32.256 satır, 1.344 benzersiz hedef saat × 24 tahmin ufkundan oluşur; 32.256 bağımsız saat değildir.
- Üç rolling-origin kıvrımının ortalama kapsaması oturum hedefinde yaklaşık 0,905, enerji hedefinde yaklaşık 0,904'tür.
- Tahmin ufku bazında üç kıvrım ortalaması kapsama aralığı: oturum hedefi 0,904–0,907; enerji hedefi 0,902–0,906.
- S1, kesin %90 garanti, fiziksel kapasite sınırı veya güvenlik garantisi olarak yorumlanmaz.

## 6. Yaklaşık saatlik yük senaryoları

Yük profilinde 07.10.2021–31.08.2022 başlangıç tarihli 65.041 uygun oturum kullanılır. Enerji, varsayılan süre boyunca eşit güçle dağıtılır:

- U100: bağlantı süresinin tamamı,
- F50: bağlantı süresinin ilk %50'si,
- F25: bağlantı süresinin ilk %25'i.

Üç senaryoda da oturum enerjisi tüm oturum bitişlerini kapsayan saat ızgarasında korunur; sayısal fark yuvarlama toleransı içinde sıfırdır. Saatlik `kWh/saat` değeri, saatlik ortalama güçle sayısal olarak eşdeğerdir; ölçülmüş anlık güç değildir.

### 6.1. Duration ve bağlantı aralığı duyarlılığı

Kaynak veri sözlüğü Duration'ı bağlantı süresi olarak tanımlar. Buna rağmen bazı satırlarda Duration ile Start/End zamanlarından hesaplanan bağlantı aralığı arasında fark vardır. Eğitim/doğrulama analiz döneminde Duration'ı bağlantı aralığından 5 dakikadan fazla kısa olan 1.879 oturum (38.765,42 kWh) bulunur. Tam veri döneminde bu sayı 1.964 oturumdur (40.017,94 kWh).

İki süre tanımıyla üretilen profillerin zirve değerleri birbirine yakındır:

| Senaryo | Duration maksimum | Bağlantı aralığı maksimum |
|---|---:|---:|
| U100 | 442,64 | 441,14 |
| F50 | 540,27 | 538,91 |
| F25 | 587,05 | 587,29 |

Bu karşılaştırma Duration'ın aktif şarj süresi olduğunu kanıtlamaz. Mevcut Duration yaklaşımı ana senaryo olarak korunmuş, bağlantı aralığı alternatifi duyarlılık analizi olarak eklenmiştir. İki yaklaşımın enerji korunumu ayrı ayrı doğrulanmıştır.

### 6.2. Yük tahmininde seviye serisi duyarlılığı

Uygulamadaki yaklaşık yük tahmini, geçmiş yaklaşık yük profilinin gün-saat şeklini başlangıç enerjisi serisinin son 168 saatlik seviyesiyle ölçeklendirir. Alternatif olarak aynı yaklaşık yük serisinin son 168 saatlik seviyesi de test edilmiştir. Üç kıvrım ortalama MAE sonuçları çok yakındır:

| Senaryo | Mevcut başlangıç enerjisi seviyesi | Alternatif yük serisi seviyesi |
|---|---:|---:|
| U100 | 35,0738 | 35,1017 |
| F50 | 40,4767 | 40,4851 |
| F25 | 45,3855 | 45,3800 |

Mevcut yöntem, U100 ana senaryosunda az farkla daha düşük MAE verdiği ve mevcut tahmin mimarisiyle tutarlı olduğu için korunmuştur. Bu tercih uygulama ve raporda açıklanmalıdır.

## 7. Streamlit uygulaması

Ana dosya `app.py` olup beş sekme içerir:

1. Oturum başlangıç tahmini,
2. Başlangıç saatine atfedilen enerji tahmini,
3. Yaklaşık saatlik yük tahmini (U100/F50/F25),
4. Model performansı,
5. Talep yoğunluğu analizi.

Uygulama B0/S1 tahminlerini açılışta mevcut eğitim/doğrulama dosyalarından hesaplar. Model performans sekmesi `outputs_modeling/rolling_origin_karsilastirma.csv` ve `outputs_modeling/model_karsilastirma_sonuclari.csv` dosyalarını okur. R1 geçersiz eski karşılaştırma olduğu için performans ekranında gösterilmez.

## 8. Ana çalışma sırası

1. `python data_validation.py`
2. `python data_cleaning.py`
3. `python eda_analysis.py`
4. `python feature_engineering.py`
5. `python model_training.py` (HGB referans modelini yeniden eğitmek istenirse)
6. `python yaklasik_yuk_profili.py`
7. `python duration_duyarlilik.py`
8. `python yuk_seviye_duyarlilik.py`
9. `python belirsizlik_ufuk_tanisi.py`
10. `python performans_ozeti_olustur.py` (arşivlenmiş rolling-origin deney CSV'lerini kullanır)
11. `streamlit run app.py`

`model_training.py` çalıştırılırsa `outputs_modeling/models/` altındaki HGB modelleri yeniden yazılır. Bu modeller scikit-learn 1.7.2 ile kaydedilmiştir; yeniden eğitim yapılmayacaksa `requirements.txt` içindeki scikit-learn sürümü korunmalıdır.

## 9. Doğrulama durumu ve kalan işler

**Tamamlanan kontroller:**

- Veri doğrulama, veri temizleme, EDA ve özellik mühendisliği betikleri yeniden çalıştırıldı.
- Ham kayıt, tekrarsız kayıt, dışlama ve saatlik veri sayıları raporla uyumlu.
- B0 rolling-origin ortalama MAE değerleri yeniden üretildi.
- HGB Eylül test değerleri kayıtlı çıktı dosyalarıyla eşleşiyor.
- S1 kapsaması tahmin ufkuna göre ayrıca hesaplandı.
- U100/F50/F25 enerji korunumu kontrol edildi.
- Duration/bağlantı aralığı ve yük seviye serisi duyarlılık deneyleri üretildi.
- Ana uygulamanın saf tahmin fonksiyonları 24 satır, sonlu B0/S1 değerleri ve S1 ≥ B0 koşuluyla test edildi.
- Python dosyalarının sözdizimi kontrolü yapıldı.
- Windows ortamında Python 3.13.7 ile sanal ortam oluşturuldu.
- `requirements.txt` içindeki kütüphaneler hatasız kuruldu ve import kontrolleri başarıyla tamamlandı.
- Streamlit uygulaması yerel ortamda başlatıldı ve tarayıcıda açıldı.
- Beş uygulama sekmesi, grafikler ve tablolar görsel olarak kontrol edildi; kritik bir çalışma hatası gözlenmedi.
- Nihai akademik rapor; Duration tanımı, R1'in dışlanması, S1 ufuk kapsaması ve yük seviyesi duyarlılığı açıklamalarıyla güncellendi.

**Son değerlendirme:**

- Uygulamanın Windows üzerinde çalıştırılması ve temel arayüz kontrolleri tamamlanmıştır.
- Streamlit tarafından `use_container_width` kullanımı için verilen kaldırılma uyarıları mevcuttur. Bunlar mevcut çalışmayı engellememektedir; ileride `width` parametresiyle güncellenebilir.
- Nihai teslimattan önce proje dosyalarının, raporun ve arşiv içeriğinin son kez kontrol edilmesi önerilir.

## 10. Kaynak

Baek, K., Lee, E., & Kim, J. (2024). *A dataset for multi-faceted analysis of electric vehicle charging transactions*. Scientific Data, 11, Article 262. https://doi.org/10.1038/s41597-024-02942-9

Kaynak veri sözlüğü Duration'ı bağlantı süresi (dakika), Demand'i oturumda araca aktarılan enerji (kWh) olarak tanımlar.
