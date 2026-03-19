# 🌊 Ankara Kentsel Sel Riski: GeoAI ile Mekansal Analiz
### ve Sosyal Kırılganlık Değerlendirmesi

**Mustafa Berk Doğru**  
Ankara Üniversitesi · Dil ve Tarih-Coğrafya Fakültesi · Coğrafya Bölümü  
📧 [İletişim](#iletişim) · 🏆 Esri Türkiye Genç Bilginler 2026

---

## 📌 Proje Özeti

Bu çalışma, Ankara Büyükşehir Belediyesi'nin 2020-2022 yıllarına ait **215 gerçek vatandaş sel ihbar noktasını** bağımlı değişken olarak kullanarak ArcGIS Pro ortamında makine öğrenmesi tabanlı kentsel sel risk haritalaması gerçekleştirmektedir.

**Türkiye'deki ilk GeoAI tabanlı kentsel pluvial sel risk sistemi** olma özelliğini taşımaktadır.

---

## 🎯 Temel Bulgular

| Metrik | Değer |
|--------|-------|
| Model | Forest-based Classification v5 |
| Spatial CV (LODO) MCC | **0.830** |
| AUC-ROC | **0.973** |
| Recall | **0.920** · F1: 0.869 |
| Bağımsız Doğrulama (Akyurt, n=76) | Recall: **0.934** · Precision: **1.000** |
| Risk Altındaki Nüfus (2023) | **666.009 kişi** (%22.1) |
| RCP 8.5 Projeksiyonu (2035) | **841.248 kişi** |

---

## 🗺️ Çalışma Alanı

**5 Merkez İlçe:** Keçiören · Çankaya · Altındağ · Yenimahalle · Akyurt

---

## 🔬 Metodoloji

### Model
- **ArcGIS Forest-based Classification v5**
- 4 değişken: Yükseklik · Eğim · Akış Birikimi · TWI
- 702 eğitim noktası (292 sel + 410 fiziksel kriter bazlı negatif örnekleme)
- 8.017 tahmin noktası

### Özgün Katkılar
1. **LODO Spatial CV** — Leave-One-District-Out mekansal çapraz doğrulama (literatürde nadir)
2. **ABB Pluvial Taşkın İhbar Verisi** — DSİ/AFAD nehir taşkını değil, gerçek kentsel altyapı verisi
3. **SHAP Açıklanabilirlik** — Yükseklik (0.325) > Akarsulara Mesafe (0.158) — Gül (2025) ile bağımsız doğrulandı
4. **Space-Time Cube + Emerging Hot Spot** — Zamansal ihbar verisi üzerinde
5. **SVI** — Türkiye'deki sel çalışmalarında ilk sosyal kırılganlık entegrasyonu

### Kullanılan ArcGIS Araçları
- Forest-based Classification
- Optimized Hot Spot Analysis
- Space-Time Cube · Emerging Hot Spot Analysis
- Zonal Statistics As Table
- IDW Interpolation · Kernel Density
- Spatial Join · Extract Multi Values to Points

---

## 📊 Veri Kaynakları

| Veri | Kaynak |
|------|--------|
| Sel İhbar Noktaları (2020-2022) | Ankara Büyükşehir Belediyesi |
| Sayısal Yükseklik Modeli (12.5m) | ALOS PALSAR |
| Uydu Görüntüleri (NDVI/NDBI) | Sentinel-2 (ESA Copernicus) |
| Nüfus Verileri | TÜİK 2022 |
| Yağış İstasyonları | MGM |
| İklim Projeksiyonları | IPCC AR6 Türkiye |
| Basemap | Esri Living Atlas · OpenStreetMap |

---

## 🛠️ Teknik Gereksinimler

```
ArcGIS Pro 3.x
  ├── Spatial Analyst Extension
  ├── 3D Analyst Extension
  └── Advanced License

Python 3.x (ArcGIS Pro ortamında)
  ├── arcpy
  ├── numpy
  ├── pandas
  ├── matplotlib
  ├── scikit-learn
  └── shap
```

---

## 📁 Dosya Yapısı

```
ankara-sel-risk-geoai/
│
├── ankara_sel_risk_FINAL_v2.py   # Ana analiz kodu (tüm bölümler)
└── README.md                     # Bu dosya
```

### Kod Yapısı (ankara_sel_risk_FINAL_v2.py)

| Bölüm | İçerik |
|-------|--------|
| 0 | Kurulum ve yollar |
| 1 | CSV → Nokta katmanı |
| 2 | DEM Birleştirme (Mosaic) |
| 3 | Türev katmanlar (Eğim, Akış, TWI, EUC_DIST) |
| 4 | Nokta birleştirme ve raster değer ekleme |
| 5 | Negatif örnekleme stratejisi |
| 6 | Eğitim verisi oluşturma |
| 7 | Veri zenginleştirme (Nüfus + Drenaj) |
| 8 | Tahmin gridi + Risk haritası |
| 9 | Forest-based Classification v5 |
| 10 | LODO Spatial CV |
| 11 | Bağımsız doğrulama |
| 12 | SHAP Analizi |
| 13 | Hotspot + Space-Time Cube + Emerging Hot Spot |
| 14 | Sosyal Kırılganlık İndeksi (SVI) |
| 15 | Zonal Statistics |
| 16 | Harita sembolojisi |
| 17 | IDW Yağış İnterpolasyonu |
| 18 | Kernel Density |
| 19 | Nüfus Risk Analizi |
| 20 | İklim Senaryosu (RCP 4.5 / RCP 8.5) |

---

## 🚀 Kullanım

```python
# ArcGIS Pro Notebook'ta çalıştır
# Her fonksiyon yorum satırı olarak kapalı — ilk çalıştırmada açın

# Örnek kullanım:
# dem_birlestir()              # Sadece ilk seferinde
# dem_turevleri_hesapla()      # Sadece ilk seferinde
# forest_modeli_egit()         # Model eğitimi
# risk_tahmini_yap(tahmin_pts) # Tahmin
# lodo_spatial_cv()            # Doğrulama
# shap_analizi()               # Açıklanabilirlik
```

---

## 📫 İletişim

**Mustafa Berk Doğru**  
Ankara Üniversitesi, Coğrafya Bölümü  

🔗 GitHub: [github.com/mustafaberkdogru](https://github.com/mustafaberkdogru)

---

## 📄 Lisans

Bu proje akademik amaçlı üretilmiştir.  
Kaynak gösterilerek kullanılabilir.

---

*Esri Türkiye Genç Bilginler 2026 · ArcGIS Pro · GeoAI · Kentsel Sel Risk*
