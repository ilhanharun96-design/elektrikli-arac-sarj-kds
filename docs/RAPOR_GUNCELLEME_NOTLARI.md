# Nihai rapor güncelleme notları

Güncellenmiş Word raporu: `Elektrikli_Arac_Sarj_KDS_Nihai_Rapor_Guncel.docx`

Bu sürümde aşağıdaki teknik düzeltmeler işlendi:

1. **Duration tanımı:** Kaynak veri sözlüğündeki Duration alanı bağlantı süresi olarak açıklandı; aktif enerji aktarım süresi veya ölçülmüş güç profili olmadığı belirtildi.
2. **U100/F50/F25:** Senaryoların bağlantı süresine dayalı eşit güç dağıtım varsayımları olduğu netleştirildi.
3. **R1 karşılaştırması:** Eski R1 deneyinde artıkların in-sample B0 tahminlerinden üretildiği ve bu nedenle adil karşılaştırma tablosundan çıkarıldığı açıklandı. R1 satırı model karşılaştırma tablosundan kaldırıldı.
4. **S1 ufuk tanısı:** Oturum ve başlangıç enerjisi hedefleri için 1–24 saat tahmin ufuklarına göre kapsama aralıkları eklendi.
5. **Duration duyarlılığı:** Duration ile bağlantı aralığı kullanılarak elde edilen yaklaşık yük zirveleri ve 1.879 oturumluk süre tutarsızlığı bulgusu eklendi.
6. **Yük seviye duyarlılığı:** Başlangıç enerjisi serisinin son 168 saatlik ortalamasıyla ölçekleme ile yaklaşık yük serisinin kendi 168 saatlik ortalaması karşılaştırıldı; mevcut yöntemin neden korunduğu açıklandı.
7. **Terminoloji:** Oturum başlangıç enerjisinin gerçek saatlik şebeke tüketimi olmadığı ve yaklaşık yük senaryolarının ölçülmüş güç profili olmadığı vurgulandı.

Rapor, proje klasöründeki `DURUM.md` ve uygulamadaki performans tablosuyla uyumlu olacak şekilde düzenlendi.
