# KDS PROJESİ - KURULUM VE ÇALIŞTIRMA KILAVUZU

## 1. Proje Hakkında

Projenin adı:
Elektrikli Araç Şarj İstasyonlarında Talep Tahmini ve Akıllı Şarj Yönetimi

Alt başlık:
Kısıtlı Güç Kapasitesi Altında Operasyonel Karar Destek Sistemi (KDS)

Bu proje, elektrikli araç şarj istasyonlarının talep yapısını incelemek,
gelecekteki talebi tahmin etmek ve kısıtlı güç kapasitesi altında
yaklaşık yük profillerini değerlendirmek amacıyla geliştirilmiştir.

Uygulama Streamlit kullanılarak hazırlanmıştır.

## 2. Sistem Gereksinimleri

- Windows 10 veya Windows 11
- Python 3.13 önerilir
- İnternet bağlantısı (ilk kurulum ve kütüphane yüklemesi için)
- Proje klasörünün tamamı

## 3. Proje Klasör Yapısı

- app.py: Streamlit karar destek sistemi uygulaması
- data/: Ham veri dosyaları
- docs/: Proje raporları ve dokümanlar
- outputs/: Veri doğrulama çıktıları
- outputs_cleaning/: Veri temizleme sonuçları
- outputs_eda/: Keşifsel veri analizi sonuçları
- outputs_feature_engineering/: Modelleme için hazırlanan veriler
- outputs_load_profile/: Yaklaşık yük profilleri ve duyarlılık analizleri
- outputs_modeling/: Model karşılaştırmaları, tahmin sonuçları ve eğitilmiş modeller
- requirements.txt: Python kütüphaneleri ve sürümleri

## 4. İlk Kurulum

PowerShell veya VS Code terminalini açın.

Önce proje klasörüne geçin. Örneğin teslimat klasörü için:

cd "$env:USERPROFILE\Desktop\KDS_Teslim"

Sanal ortam oluşturun:

python -m venv .venv

Sanal ortamı etkinleştirin:

.\.venv\Scripts\Activate.ps1

Gerekli kütüphaneleri yükleyin:

python -m pip install -r requirements.txt

Not: PowerShell yürütme politikası nedeniyle etkinleştirme engellenirse,
yalnızca mevcut terminal oturumu için şu komutu çalıştırıp yeniden deneyin:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

## 5. Uygulamayı Çalıştırma

Sanal ortam etkin durumdayken:

python -m streamlit run app.py

Uygulama genellikle şu adreste açılır:

http://localhost:8501

Tarayıcı otomatik açılmazsa bu adresi tarayıcıya kendiniz yazabilirsiniz.

## 6. Uygulamayı Durdurma

Uygulamanın çalıştığı terminal penceresine dönün ve:

Ctrl + C

tuşlarına basın.

## 7. Önemli Notlar

- Uygulamayı çalıştırmadan önce doğru proje klasöründe olduğunuzdan emin olun.
- İlk kurulumda sanal ortam oluşturulmalı ve requirements.txt yüklenmelidir.
- .venv klasörü Python çalışma ortamıdır; kaynak kodların yerine geçmez.
- Ham veri dosyalarını ve outputs klasörlerindeki sonuçları silmeyin.
- outputs_modeling/models klasöründeki eğitilmiş model dosyalarını koruyun.
- Proje dosyalarının ve klasörlerinin isimlerini değiştirmek uygulamanın dosya yollarını bozabilir.
- Ana uygulama app.py dosyasıdır.
- archive klasörü geçmiş deneysel çalışmalar ve eski uygulamalar için ayrılmıştır; ana uygulamanın çalışması için gerekli değildir.

## 8. Sık Karşılaşılan Sorunlar

### Python bulunamadı
Python kurulumunu kontrol edin:

python --version

### Kütüphane bulunamadı
Sanal ortamın etkin olduğunu kontrol edin ve tekrar yükleyin:

python -m pip install -r requirements.txt

### Uygulama dosyaları bulunamadı
Terminalin proje ana klasöründe olduğundan emin olun.

### Port kullanımda
8501 portu başka bir uygulama tarafından kullanılıyorsa Streamlit farklı bir port önerebilir. Terminalde belirtilen yerel adresi açın.

## 9. Proje Durumu

Bu proje klasöründeki mevcut uygulama, Python 3.13.7 ve requirements.txt
içindeki kütüphanelerle test edilmiştir.

Teslimat kopyasında uygulamanın bağımsız sanal ortamı oluşturulmuş,
kütüphaneleri yüklenmiş ve Streamlit arayüzü başarıyla çalıştırılmıştır.
