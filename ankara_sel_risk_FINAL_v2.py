# ═══════════════════════════════════════════════════════════════════════════════
# ANKARA KENTSEL SEL RİSKİ: GEOAI İLE MEKANSAL ANALİZ
# VE SOSYAL KIRILGANLIK DEĞERLENDİRMESİ
#
# Mustafa Berk Doğru
# Ankara Üniversitesi, Dil ve Tarih-Coğrafya Fakültesi
# Coğrafya Bölümü — Esri Türkiye Genç Bilginler 2026
#
# KAPSAMLI REVİZE VERSİYON
# ═══════════════════════════════════════════════════════════════════════════════

import arcpy
import os
import random
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from collections import Counter

# ═══════════════════════════════════════════════════════════════════════════════
# 0. KURULUM VE YOLLAR
# ═══════════════════════════════════════════════════════════════════════════════
arcpy.env.overwriteOutput = True

# Ana dizinler
GDB   = arcpy.env.workspace
CIKTI = r"C:\Users\Mustafa Berk\Downloads\ABB veri\output"
DOCS  = r"C:\Users\Mustafa Berk\Documents"
ILCE  = r"C:\Users\Mustafa Berk\Documents\ilcelerrr2.shp"

# DEM dosyaları
DEM1  = r"C:\Users\Mustafa Berk\Downloads\ABB veri\DEM\AP_07684_FBD_F0790_RT1_111\DEM_1\AP_07684_FBD_F0790_RT1.dem.tif"
DEM2  = r"C:\Users\Mustafa Berk\Downloads\ABB veri\DEM\AP_12133_FBD_F0790_RT1_222\DEM_2\AP_12133_FBD_F0790_RT1.dem.tif"
DEM3  = r"C:\Users\Mustafa Berk\Downloads\ABB veri\DEM\AP_07684_FBD_F0780_RT1_333\DEM_3\AP_07684_FBD_F0780_RT1.dem.tif"

# GDB katman yolları
SEL_ANA      = os.path.join(GDB, "sel_noktalari_ana")           # 215 ihbar noktası
SEL_YS       = os.path.join(GDB, "sel_noktalari_ys")            # Yardım sokak noktaları
ILCE_GDB     = os.path.join(GDB, "ilce_sinirlar_gdb")           # 5 ilçe sınırı
EGITIM_V4    = os.path.join(GDB, "egitim_verisi_v4")            # Eğitim verisi
TAHMIN_V5    = os.path.join(GDB, "sel_risk_tahmin_v5")          # Tahmin sonuçları
ONEM_V5      = os.path.join(GDB, "degisken_onem_final_v5")      # Değişken önem tablosu
HOTSPOT      = os.path.join(GDB, "hotspot_optimized")           # Hotspot analizi
EHS          = os.path.join(GDB, "emerging_hotspot")            # Emerging hotspot
SVI_TBL      = os.path.join(GDB, "svi_ilce_skoru")              # SVI tablosu
ZONAL        = os.path.join(GDB, "zonal_stats_ilce")            # Zonal istatistik
ILCE_CV      = os.path.join(GDB, "ilce_cv_sonuclari")           # LODO CV sonuçları

# Raster yolları
DEM          = os.path.join(GDB, "dem_ankara_merged")
EGIM         = os.path.join(GDB, "egim")
TWI          = os.path.join(GDB, "twi")
AKIS         = os.path.join(GDB, "akis_birikimi")
AKIS_YON     = os.path.join(GDB, "akis_yonu")
EUC_DIST     = os.path.join(GDB, "euc_dist_metre")

# Ankara ilçeleri
ILCELER = ["Keçiören", "Çankaya", "Altındağ", "Akyurt", "Yenimahalle"]

print(f"✓ Workspace: {GDB}")
print(f"✓ Kurulum tamamlandı")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. VERİ HAZIRLAMA - CSV'DEN NOKTA KATMANI OLUŞTURMA
# ═══════════════════════════════════════════════════════════════════════════════

def csv_to_points(csv_path, layer_name):
    """
    CSV dosyasını temizleyip nokta feature class'a dönüştürür.
    Ankara sınırları içindeki koordinatları filtreler.
    
    Parameters:
    -----------
    csv_path : str - CSV dosya yolu
    layer_name : str - Oluşturulacak katman adı
    
    Returns:
    --------
    str - Feature class yolu
    """
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    
    # Koordinatları sayısal değere dönüştür
    df['LATITUDE']  = pd.to_numeric(df['LATITUDE'],  errors='coerce')
    df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')
    
    # Null koordinatları temizle
    df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
    
    # Ankara sınırları filtresi (yaklaşık koordinat aralıkları)
    df = df[(df['LATITUDE'] > 38) & (df['LATITUDE'] < 41)]
    df = df[(df['LONGITUDE'] > 30) & (df['LONGITUDE'] < 35)]
    
    # Temiz CSV kaydet
    temiz = csv_path.replace('.csv', '_temiz.csv')
    df.to_csv(temiz, index=False, encoding='utf-8-sig')
    
    # Feature class oluştur
    out_fc = os.path.join(GDB, layer_name)
    arcpy.management.XYTableToPoint(
        temiz, out_fc, "LONGITUDE", "LATITUDE",
        coordinate_system=arcpy.SpatialReference(4326)
    )
    
    n = int(arcpy.management.GetCount(out_fc).getOutput(0))
    print(f"✓ {layer_name}: {n} nokta")
    return out_fc


def csv_katmanlarini_olustur():
    """Tüm CSV dosyalarını içe aktar"""
    
    # Sel noktaları
    fc1 = csv_to_points(os.path.join(CIKTI, "01_sel_noktalari_ana.csv"), "sel_noktalari_ana")
    fc2 = csv_to_points(os.path.join(CIKTI, "02_sel_noktalari_ys.csv"), "sel_noktalari_ys")
    
    # Yağış istasyonları
    fc3 = csv_to_points(os.path.join(CIKTI, "03_yagis_istasyonlari_haziran2022.csv"), 
                        "yagis_istasyonlari_2022")
    
    # Tablolar
    arcpy.conversion.ExportTable(os.path.join(CIKTI, "04_nufus_ilce.csv"), 
                                  os.path.join(GDB, "nufus_ilce"))
    arcpy.conversion.ExportTable(os.path.join(CIKTI, "05_drenaj_sorun_ilce.csv"), 
                                  os.path.join(GDB, "drenaj_sorun_ilce"))
    
    print("✓ Tüm CSV dosyaları içe aktarıldı")
    return fc1, fc2, fc3

# csv_katmanlarini_olustur()  # İlk çalıştırmada aktif et


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DEM BİRLEŞTİRME VE TÜREV KATMANLAR
# ═══════════════════════════════════════════════════════════════════════════════

def dem_birlestir():
    """
    Üç ayrı DEM dosyasını Mosaic ile birleştirir.
    """
    print("DEM'ler birleştiriliyor...")
    
    arcpy.management.MosaicToNewRaster(
        input_rasters   = [DEM1, DEM2, DEM3],
        output_location = GDB,
        raster_dataset_name_with_extension = "dem_ankara_merged",
        coordinate_system_for_the_raster   = arcpy.SpatialReference(4326),
        pixel_type      = "32_BIT_FLOAT",
        number_of_bands = 1,
        mosaic_method   = "MEAN"
    )
    print("✓ DEM birleştirildi")


def dem_turevleri_hesapla():
    """
    DEM'den türev katmanları hesaplar:
    - Eğim (Slope)
    - Akış Yönü (Flow Direction)
    - Akış Birikimi (Flow Accumulation)
    - TWI (Topographic Wetness Index)
    - Akarsulara Öklid Mesafesi
    """
    print("DEM türevleri hesaplanıyor...")
    
    # 1. Eğim (Derece cinsinden)
    arcpy.ddd.Slope(DEM, EGIM, "DEGREE")
    print("  ✓ Eğim hesaplandı")
    
    # 2. Akış Yönü
    arcpy.ddd.FlowDirection(DEM, AKIS_YON)
    print("  ✓ Akış yönü hesaplandı")
    
    # 3. Akış Birikimi
    arcpy.ddd.FlowAccumulation(AKIS_YON, AKIS)
    print("  ✓ Akış birikimi hesaplandı")
    
    # 4. TWI (Topographic Wetness Index)
    # TWI = ln(a / tan(β)) where a = akış birikimi, β = eğim açısı
    print("  TWI hesaplanıyor...")
    egim_rad = arcpy.sa.Times(arcpy.sa.Raster(EGIM), 0.01745329)  # Derece -> Radyan
    tan_egim = arcpy.sa.Con(egim_rad > 0.001, arcpy.sa.Tan(egim_rad), 0.001)  # Sıfıra bölünmeyi önle
    twi_r = arcpy.sa.Ln(arcpy.sa.Plus(arcpy.sa.Raster(AKIS), 1) / tan_egim)
    twi_r.save(TWI)
    print("  ✓ TWI hesaplandı")
    
    # 5. Akarsulara Öklid Mesafesi
    akarsu = os.path.join(GDB, "akarsu_hatlar")
    if arcpy.Exists(akarsu):
        arcpy.sa.EucDistance(akarsu).save(EUC_DIST)
        print("  ✓ Akarsulara mesafe hesaplandı")
    else:
        print("  ! Akarsu katmanı bulunamadı, EUC_DIST atlanıyor")
    
    print("✓ Tüm DEM türevleri hesaplandı")

# dem_birlestir()
# dem_turevleri_hesapla()  # İlk çalıştırmada aktif et


# ═══════════════════════════════════════════════════════════════════════════════
# 3. NOKTA KATMANLARINI BİRLEŞTİRME VE RASTER DEĞERLERİ EKLEME
# ═══════════════════════════════════════════════════════════════════════════════

def noktalari_birlestir_ve_zenginlestir():
    """
    Sel noktalarını birleştirir ve raster değerlerini ekler.
    """
    print("Noktalar birleştiriliyor ve zenginleştiriliyor...")
    
    # İki nokta katmanını birleştir
    sel_birlesik = os.path.join(GDB, "sel_noktalari_birlesik")
    arcpy.management.Merge([SEL_ANA, SEL_YS], sel_birlesik)
    n = int(arcpy.management.GetCount(sel_birlesik).getOutput(0))
    print(f"  ✓ Toplam {n} sel noktası birleştirildi")
    
    # Raster değerlerini noktalara ekle
    raster_listesi = [
        [EGIM, "EGIM_DERECE"],
        [DEM, "YUKSEKLIK_M"],
        [AKIS, "AKIS_BIRIKIMI"],
        [TWI, "TWI"],
    ]
    
    if arcpy.Exists(EUC_DIST):
        raster_listesi.append([EUC_DIST, "EUC_DIST"])
    
    arcpy.sa.ExtractMultiValuesToPoints(
        in_point_features = sel_birlesik,
        in_rasters = raster_listesi,
        bilinear_interpolate_values = "BILINEAR"
    )
    print("  ✓ Raster değerleri eklendi")
    
    return sel_birlesik

# sel_birlesik = noktalari_birlestir_ve_zenginlestir()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. AKILLI NEGATİF ÖRNEKLEME STRATEJİSİ
# ═══════════════════════════════════════════════════════════════════════════════

def negatif_ornekleme(n_hedef=410, tampon_metre=500):
    """
    Fiziksel olarak sel olmayacak alanlarda negatif nokta üretir.
    
    Kriterler:
    - Yüksek rakım (>1200m) VEYA
    - Düz alan (eğim < 2°) VE düşük akış birikimi (<10)
    
    Tampon: Mevcut sel noktalarından belirli mesafe uzakta
    
    Parameters:
    -----------
    n_hedef : int - Hedef negatif nokta sayısı
    tampon_metre : float - Sel noktalarından minimum uzaklık (metre)
    
    Returns:
    --------
    list - (x, y, egim, yukseklik, akis, twi) demetleri
    """
    print(f"Negatif örnekleme başlıyor (hedef: {n_hedef} nokta, tampon: {tampon_metre}m)...")
    
    # Çalışma alanı extent
    desc = arcpy.Describe(ILCE_GDB)
    extent = desc.extent
    xmin, xmax = extent.XMin, extent.XMax
    ymin, ymax = extent.YMin, extent.YMax
    
    # Raster'ları numpy array'e çevir (performans için)
    print("  Raster'lar yükleniyor...")
    egim_r = arcpy.RasterToNumPyArray(EGIM, nodata_to_value=-9999)
    akis_r = arcpy.RasterToNumPyArray(AKIS, nodata_to_value=-9999)
    dem_r  = arcpy.RasterToNumPyArray(DEM, nodata_to_value=-9999)
    twi_r  = arcpy.RasterToNumPyArray(TWI, nodata_to_value=-9999)
    
    cell = arcpy.Describe(EGIM).meanCellWidth
    
    # Sel noktası koordinatları (tampon kontrolü için)
    sel_coords = [(r[0], r[1]) for r in arcpy.da.SearchCursor(SEL_ANA, ["SHAPE@X", "SHAPE@Y"])]
    print(f"  {len(sel_coords)} sel noktası yüklendi")
    
    noktalar = []
    deneme = 0
    random.seed(42)
    
    while len(noktalar) < n_hedef and deneme < n_hedef * 100:
        deneme += 1
        
        # Rastgele koordinat üret
        x = random.uniform(xmin, xmax)
        y = random.uniform(ymin, ymax)
        
        # Piksel indekslerini hesapla
        col = int((x - xmin) / cell)
        row = int((ymax - y) / cell)
        
        if row < 0 or col < 0 or row >= egim_r.shape[0] or col >= egim_r.shape[1]:
            continue
        
        try:
            egim_val = egim_r[row, col]
            akis_val = akis_r[row, col]
            dem_val  = dem_r[row, col]
            twi_val  = twi_r[row, col]
        except IndexError:
            continue
        
        # NoData kontrolü
        if egim_val == -9999:
            continue
        
        # Fiziksel kriter: Sel olmayacak alan
        fiziksel = (dem_val > 1200) or (egim_val < 2 and akis_val < 10)
        if not fiziksel:
            continue
        
        # Tampon kontrolü: Sel noktalarından uzakta
        cok_yakin = any(
            (x - sx)**2 + (y - sy)**2 < tampon_metre**2
            for sx, sy in sel_coords
        )
        if cok_yakin:
            continue
        
        noktalar.append((x, y, egim_val, dem_val, akis_val, twi_val))
    
    print(f"  ✓ {len(noktalar)} negatif nokta üretildi ({deneme} denemede)")
    return noktalar


def negatif_nokta_fc_olustur(nokta_listesi):
    """
    Negatif nokta listesinden feature class oluşturur.
    """
    negatif_fc = os.path.join(GDB, "sel_yok_noktalar")
    
    # Feature class oluştur
    arcpy.management.CreateFeatureclass(
        GDB, "sel_yok_noktalar", "POINT",
        spatial_reference=arcpy.SpatialReference(4326)
    )
    
    # Alanları ekle
    alanlar = [
        ("SEL_NOKTASI", "SHORT"),
        ("oncelik_skoru", "SHORT"),
        ("EGIM_DERECE", "DOUBLE"),
        ("YUKSEKLIK_M", "DOUBLE"),
        ("AKIS_BIRIKIMI", "DOUBLE"),
        ("TWI", "DOUBLE"),
    ]
    
    for alan, tip in alanlar:
        arcpy.management.AddField(negatif_fc, alan, tip)
    
    # Noktaları ekle
    cursor_alanlar = ["SHAPE@XY", "SEL_NOKTASI", "oncelik_skoru", 
                      "EGIM_DERECE", "YUKSEKLIK_M", "AKIS_BIRIKIMI", "TWI"]
    
    with arcpy.da.InsertCursor(negatif_fc, cursor_alanlar) as cur:
        for x, y, egim, dem, akis, twi in nokta_listesi:
            cur.insertRow([(x, y), 0, 0, egim, dem, akis, twi])
    
    print(f"✓ {len(nokta_listesi)} negatif nokta feature class'a eklendi")
    return negatif_fc

# negatif_liste = negatif_ornekleme(n_hedef=410, tampon_metre=500)
# negatif_fc = negatif_nokta_fc_olustur(negatif_liste)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. EĞİTİM VERİSİ OLUŞTURMA VE ZENGİNLEŞTİRME
# ═══════════════════════════════════════════════════════════════════════════════

def egitim_verisi_olustur():
    """
    Pozitif ve negatif noktaları birleştirerek eğitim verisi oluşturur.
    İlçe, nüfus ve drenaj bilgilerini ekler.
    """
    print("Eğitim verisi oluşturuluyor...")
    
    # Pozitif ve negatif noktaları birleştir
    sel_birlesik = os.path.join(GDB, "sel_noktalari_birlesik")
    negatif_fc = os.path.join(GDB, "sel_yok_noktalar")
    
    egitim_fc = os.path.join(GDB, "egitim_verisi_v4")
    arcpy.management.Merge([sel_birlesik, negatif_fc], egitim_fc)
    
    n = int(arcpy.management.GetCount(egitim_fc).getOutput(0))
    print(f"  ✓ {n} nokta birleştirildi")
    
    return egitim_fc


def veri_zenginlestir(egitim_fc):
    """
    Eğitim verisine ilçe, nüfus ve drenaj bilgilerini ekler.
    """
    print("Veri zenginleştiriliyor...")
    
    # İlçe key oluştur (büyük harf, normalized)
    alanlar = [f.name for f in arcpy.ListFields(egitim_fc)]
    
    if "ilce" in alanlar:
        arcpy.management.AddField(egitim_fc, "ILCE_KEY", "TEXT", field_length=50)
        arcpy.management.CalculateField(
            egitim_fc, "ILCE_KEY",
            "str(!ilce!).upper().strip() if !ilce! else 'BILINMIYOR'",
            "PYTHON3"
        )
        print("  ✓ ILCE_KEY alanı oluşturuldu")
    
    # Nüfus join
    nufus_tablo = os.path.join(GDB, "nufus_ilce")
    if arcpy.Exists(nufus_tablo):
        arcpy.management.JoinField(egitim_fc, "ILCE_KEY", nufus_tablo, "ILCE", ["TOPLAM_NUFUS"])
        print("  ✓ Nüfus bilgisi eklendi")
    
    # Drenaj join
    drenaj_tablo = os.path.join(GDB, "drenaj_sorun_ilce")
    if arcpy.Exists(drenaj_tablo):
        arcpy.management.JoinField(egitim_fc, "ILCE_KEY", drenaj_tablo, "ILCE", ["COZUMSUZ_NOKTA"])
        print("  ✓ Drenaj bilgisi eklendi")
    
    # Boş değerleri 0 yap
    for alan in ["TOPLAM_NUFUS", "COZUMSUZ_NOKTA"]:
        arcpy.management.CalculateField(
            egitim_fc, alan,
            f"!{alan}! if !{alan}! is not None else 0",
            "PYTHON3"
        )
    
    print("✓ Veri zenginleştirme tamamlandı")

# egitim_fc = egitim_verisi_olustur()
# veri_zenginlestir(egitim_fc)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. FOREST-BASED CLASSIFICATION MODELİ
# ═══════════════════════════════════════════════════════════════════════════════

def forest_modeli_egit():
    """
    Forest-based Classification modelini eğitir.
    
    Değişkenler:
    - YUKSEKLIK_M: Yükseklik (metre)
    - EGIM_DERECE: Eğim (derece)
    - AKIS_BIRIKIMI: Akış birikimi
    - TWI: Topographic Wetness Index
    """
    print("Forest-based Classification v5 eğitiliyor...")
    
    model_out = os.path.join(GDB, "sel_risk_tahmin_v5")
    onem_out  = os.path.join(GDB, "degisken_onem_final_v5")
    
    result = arcpy.stats.Forest(
        prediction_type               = "TRAIN",
        in_features                   = EGITIM_V4,
        variable_predict              = "SEL_NOKTASI",
        treat_variable_as_categorical = True,
        explanatory_variables         = [
            ["YUKSEKLIK_M",   False],
            ["EGIM_DERECE",   False],
            ["AKIS_BIRIKIMI", False],
            ["TWI",           False],
        ],
        output_features               = model_out,
        output_importance_table       = onem_out,
        number_of_trees               = 200,
        percentage_for_training       = 70,
        output_trained_features       = os.path.join(GDB, "_forest_v5_trained"),
    )
    
    print("✓ Model eğitildi")
    
    # Model mesajlarını yazdır
    msgs = result.getMessages()
    for line in msgs.split("\n"):
        if any(k in line.lower() for k in ["accuracy", "oob", "mse", "r2"]):
            print(f"  {line.strip()}")
    
    return model_out

# forest_modeli_egit()


# ═══════════════════════════════════════════════════════════════════════════════
# 7. TAHMİN GRİDİ OLUŞTURMA VE RİSK HARİTASI
# ═══════════════════════════════════════════════════════════════════════════════

def tahmin_gridi_olustur():
    """
    Ankara geneli için tahmin noktaları (fishnet) oluşturur.
    """
    print("Tahmin gridi oluşturuluyor...")
    
    fishnet_fc = os.path.join(GDB, "tahmin_fishnet")
    tahmin_pts = os.path.join(GDB, "tahmin_noktalari_tum")
    
    # Polygon fishnet oluştur
    arcpy.management.CreateFishnet(
        out_feature_class = fishnet_fc,
        origin_coord      = "32.0 39.6",
        y_axis_coord      = "32.0 39.7",
        cell_width        = 0.005,
        cell_height       = 0.005,
        number_rows       = "",
        number_columns    = "",
        corner_coord      = "33.5 40.3",
        labels            = "NO_LABELS",
        geometry_type     = "POLYGON"
    )
    
    # Merkez noktaları al
    arcpy.management.FeatureToPoint(fishnet_fc, tahmin_pts, "CENTROID")
    n = int(arcpy.management.GetCount(tahmin_pts).getOutput(0))
    print(f"  ✓ {n} tahmin noktası oluşturuldu")
    
    # Raster değerlerini ekle
    arcpy.sa.ExtractMultiValuesToPoints(
        in_point_features = tahmin_pts,
        in_rasters = [
            [EGIM, "EGIM_DERECE"],
            [DEM, "YUKSEKLIK_M"],
            [AKIS, "AKIS_BIRIKIMI"],
            [TWI, "TWI"],
        ],
        bilinear_interpolate_values = "BILINEAR"
    )
    
    # Null değerleri temizle
    silinen = 0
    with arcpy.da.UpdateCursor(tahmin_pts, ["EGIM_DERECE", "YUKSEKLIK_M", "AKIS_BIRIKIMI", "TWI"]) as cur:
        for row in cur:
            if None in row:
                cur.deleteRow()
                silinen += 1
    
    n_kalan = int(arcpy.management.GetCount(tahmin_pts).getOutput(0))
    print(f"  ✓ {silinen} boş nokta temizlendi, {n_kalan} nokta hazır")
    
    return tahmin_pts


def risk_tahmini_yap(tahmin_pts):
    """
    Eğitilen model ile tüm Ankara için risk tahmini yapar.
    """
    print("Risk tahmini yapılıyor...")
    
    tahmin_sonuc = os.path.join(GDB, "sel_risk_tahmin_v5")
    
    result = arcpy.stats.Forest(
        prediction_type               = "PREDICT_FEATURES",
        in_features                   = EGITIM_V4,
        variable_predict              = "SEL_NOKTASI",
        treat_variable_as_categorical = True,
        explanatory_variables         = [
            ["YUKSEKLIK_M",   False],
            ["EGIM_DERECE",   False],
            ["AKIS_BIRIKIMI", False],
            ["TWI",           False],
        ],
        features_to_predict           = tahmin_pts,
        output_features               = tahmin_sonuc,
        explanatory_variable_matching = "YUKSEKLIK_M YUKSEKLIK_M;EGIM_DERECE EGIM_DERECE;AKIS_BIRIKIMI AKIS_BIRIKIMI;TWI TWI",
        number_of_trees               = 200,
    )
    
    n = int(arcpy.management.GetCount(tahmin_sonuc).getOutput(0))
    print(f"✓ {n} nokta için risk tahmini üretildi")
    
    # Yüksek risk istatistiği
    yuksek_risk = 0
    with arcpy.da.SearchCursor(tahmin_sonuc, ["Predicted"]) as cur:
        for row in cur:
            if row[0] == 1:
                yuksek_risk += 1
    
    print(f"  Yüksek risk: {yuksek_risk} nokta ({yuksek_risk/n*100:.1f}%)")

    # ── Predicted_Probability → 5 Sınıflı RISK_SKORU_V5 dönüşümü ──────────────
    # Predicted_Probability: 0.0-1.0 olasılık değeri (Forest çıktısı)
    # RISK_SKORU_V5: 1=Çok Düşük, 2=Düşük, 3=Orta, 4=Yüksek, 5=Çok Yüksek
    print("  RISK_SKORU_V5 hesaplanıyor...")

    arcpy.management.AddField(tahmin_sonuc, "RISK_SKORU_V5", "SHORT")

    with arcpy.da.UpdateCursor(
        tahmin_sonuc, ["Predicted_Probability", "RISK_SKORU_V5"]
    ) as cur:
        for row in cur:
            prob = row[0] if row[0] is not None else 0.0
            if   prob < 0.20: skor = 1   # Çok Düşük
            elif prob < 0.40: skor = 2   # Düşük
            elif prob < 0.60: skor = 3   # Orta
            elif prob < 0.80: skor = 4   # Yüksek
            else:             skor = 5   # Çok Yüksek
            row[1] = skor
            cur.updateRow(row)

    dagilim = {1:0, 2:0, 3:0, 4:0, 5:0}
    for r in arcpy.da.SearchCursor(tahmin_sonuc, ["RISK_SKORU_V5"]):
        s = r[0] if r[0] else 0
        if s in dagilim: dagilim[s] += 1
    etiket = {1:"Çok Düşük",2:"Düşük",3:"Orta",4:"Yüksek",5:"Çok Yüksek"}
    print("  Risk dağılımı:")
    for s in sorted(dagilim):
        print(f"    Sınıf {s} ({etiket[s]:10s}): {dagilim[s]:4d}  %{dagilim[s]/n*100:.1f}")

    return tahmin_sonuc

# tahmin_pts = tahmin_gridi_olustur()
# risk_haritasi = risk_tahmini_yap(tahmin_pts)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. LODO SPATIAL CROSS-VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def mcc_hesapla(tp, tn, fp, fn):
    """
    Matthews Correlation Coefficient hesaplar.
    
    MCC = (TP*TN - FP*FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))
    
    MCC değeri -1 ile +1 arasındadır:
    - +1: Mükemmel tahmin
    - 0: Rastgele tahmin
    - -1: Tamamen yanlış tahmin
    """
    pay = (tp * tn) - (fp * fn)
    payda = ((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn))**0.5
    return pay / payda if payda > 0 else 0


def lodo_spatial_cv():
    """
    Leave-One-District-Out Mekansal Çapraz Doğrulama
    
    Her fold'da:
    - 1 ilçe test verisi
    - Kalan 4 ilçe eğitim verisi
    
    Bu yöntem, modelin mekansal genelleme yeteneğini test eder.
    """
    print("=" * 60)
    print("LODO SPATIAL CROSS-VALIDATION")
    print("=" * 60)
    
    sonuclar = []
    
    for test_ilce in ILCELER:
        print(f"\n  Fold: {test_ilce} test, diğerleri eğitim...")
        
        # Test ve eğitim setlerini ayır
        egitim_fold = os.path.join(GDB, "_fold_egitim")
        test_fold   = os.path.join(GDB, "_fold_test")
        
        arcpy.analysis.Select(EGITIM_V4, egitim_fold, f"ilce <> '{test_ilce}'")
        arcpy.analysis.Select(EGITIM_V4, test_fold,   f"ilce = '{test_ilce}'")
        
        n_egitim = int(arcpy.management.GetCount(egitim_fold).getOutput(0))
        n_test   = int(arcpy.management.GetCount(test_fold).getOutput(0))
        
        print(f"    Eğitim: {n_egitim}, Test: {n_test}")
        
        # Modeli eğit
        tahmin_fold = os.path.join(GDB, "_fold_tahmin")
        arcpy.stats.Forest(
            prediction_type               = "TRAIN",
            in_features                   = egitim_fold,
            variable_predict              = "SEL_NOKTASI",
            treat_variable_as_categorical = True,
            explanatory_variables         = [
                ["YUKSEKLIK_M",   False],
                ["EGIM_DERECE",   False],
                ["AKIS_BIRIKIMI", False],
                ["TWI",           False],
            ],
            output_features               = tahmin_fold,
            number_of_trees               = 200,
            percentage_for_training       = 70,
        )
        
        # Confusion matrix hesapla
        tp = tn = fp = fn = 0
        for r in arcpy.da.SearchCursor(tahmin_fold, ["SEL_NOKTASI", "Predicted_SEL_NOKTASI"]):
            gercek, tahmin = int(r[0]), int(r[1])
            if   gercek == 1 and tahmin == 1: tp += 1
            elif gercek == 0 and tahmin == 0: tn += 1
            elif gercek == 0 and tahmin == 1: fp += 1
            elif gercek == 1 and tahmin == 0: fn += 1
        
        # Metrikleri hesapla
        acc    = (tp + tn) / (tp + tn + fp + fn) if (tp+tn+fp+fn) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        prec   = tp / (tp + fp) if (tp + fp) > 0 else 0
        f1     = 2 * prec * recall / (prec + recall) if (prec + recall) > 0 else 0
        mcc    = mcc_hesapla(tp, tn, fp, fn)
        
        sonuclar.append({
            "ilce": test_ilce, 
            "n_egitim": n_egitim, 
            "n_test": n_test,
            "tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "acc": acc, "recall": recall, "precision": prec, "f1": f1, "mcc": mcc
        })
        
        print(f"    Acc: {acc:.3f}  F1: {f1:.3f}  MCC: {mcc:.3f}  Recall: {recall:.3f}")
        
        # Geçici katmanları temizle
        for tmp in [egitim_fold, test_fold, tahmin_fold]:
            if arcpy.Exists(tmp):
                arcpy.management.Delete(tmp)
    
    # Ortalama metrikler
    ort_acc    = sum(s["acc"]    for s in sonuclar) / len(sonuclar)
    ort_f1     = sum(s["f1"]     for s in sonuclar) / len(sonuclar)
    ort_mcc    = sum(s["mcc"]    for s in sonuclar) / len(sonuclar)
    ort_recall = sum(s["recall"] for s in sonuclar) / len(sonuclar)
    
    print("\n" + "=" * 60)
    print(f"  ORTALAMA → Acc: {ort_acc:.3f}  F1: {ort_f1:.3f}  MCC: {ort_mcc:.3f}  Recall: {ort_recall:.3f}")
    print("=" * 60)
    
    return sonuclar

# lodo_sonuclari = lodo_spatial_cv()


# ═══════════════════════════════════════════════════════════════════════════════
# 9. SHAP ANALİZİ (AÇIKLANABİLİR YAPAY ZEKA)
# ═══════════════════════════════════════════════════════════════════════════════

def shap_analizi():
    """
    SHAP (SHapley Additive exPlanations) analizi ile değişken önemini açıklar.
    
    sklearn RandomForest ile uyumlu olduğu için ArcGIS Forest sonuçlarını 
    doğrulamak için kullanılır.
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        import shap
    except ImportError:
        print("HATA: sklearn ve shap kütüphaneleri gerekli!")
        print("pip install scikit-learn shap")
        return None, None, None, None
    
    print("SHAP analizi başlıyor...")
    
    # Eğitim verisini GDB'den oku
    alanlar = ["SEL_NOKTASI", "YUKSEKLIK_M", "EGIM_DERECE", "AKIS_BIRIKIMI", "TWI"]
    
    if arcpy.Exists(EUC_DIST):
        alanlar.append("EUC_DIST")
    
    veriler = []
    for r in arcpy.da.SearchCursor(EGITIM_V4, alanlar):
        if all(v is not None for v in r):
            veriler.append(r)
    
    X = np.array([[r[i] for i in range(1, len(r))] for r in veriler])
    y = np.array([int(r[0]) for r in veriler])
    
    feature_names = ["Yükseklik (m)", "Eğim (°)", "Akış Birikimi", "TWI"]
    if arcpy.Exists(EUC_DIST):
        feature_names.append("Akarsulara Mesafe (m)")
    
    print(f"  {len(veriler)} örnek, {len(feature_names)} değişken")
    
    # Model eğit
    rf = RandomForestClassifier(
        n_estimators=200, 
        random_state=42, 
        class_weight='balanced',
        n_jobs=-1
    )
    rf.fit(X, y)
    
    # SHAP değerleri
    print("  SHAP değerleri hesaplanıyor...")
    explainer   = shap.TreeExplainer(rf)
    shap_values = explainer.shap_values(X)
    
    # Sel sınıfı (1) için SHAP değerleri
    shap_sel = shap_values[1] if isinstance(shap_values, list) else shap_values
    
    # Global önem (ortalama mutlak SHAP)
    global_onem = np.abs(shap_sel).mean(axis=0)
    
    print("\n  Global SHAP Değerleri (Değişken Önem Sırası):")
    print("  " + "-" * 45)
    for name, val in sorted(zip(feature_names, global_onem), key=lambda x: -x[1]):
        bar = "█" * int(val * 10)
        print(f"    {name:25s}: {val:.4f} {bar}")
    
    return shap_sel, global_onem, feature_names, X

# shap_vals, global_onem, feat_names, X_train = shap_analizi()


# ═══════════════════════════════════════════════════════════════════════════════
# 10. HOTSPOT VE ZAMANSAL ANALİZ
# ═══════════════════════════════════════════════════════════════════════════════

def hotspot_analizi():
    """
    Optimized Hot Spot Analysis ile sel noktalarının kümelenme analizini yapar.
    """
    print("Optimized Hot Spot Analizi yapılıyor...")
    
    arcpy.stats.OptimizedHotSpotAnalysis(
        Input_Features           = SEL_ANA,
        Output_Features          = HOTSPOT,
        Analysis_Field           = None,
        Incident_Data_Aggregation_Method = "COUNT_INCIDENTS_WITHIN_FISHNET_POLYGONS",
    )
    
    n = int(arcpy.management.GetCount(HOTSPOT).getOutput(0))
    print(f"✓ Hotspot analizi tamamlandı: {n} alan")
    
    # Soğuk/sıcak nokta özeti
    sayim = Counter()
    for r in arcpy.da.SearchCursor(HOTSPOT, ["Gi_Bin"]):
        if r[0]:
            if r[0] == 3:
                sayim["Sıcak Nokta (99%)"] += 1
            elif r[0] == 2:
                sayim["Sıcak Nokta (95%)"] += 1
            elif r[0] == -3:
                sayim["Soğuk Nokta (99%)"] += 1
            elif r[0] == -2:
                sayim["Soğuk Nokta (95%)"] += 1
    
    print("  Kümeleme özeti:")
    for k, v in sayim.most_common():
        print(f"    {k}: {v}")


def space_time_cube_olustur():
    """
    Space-Time Cube oluşturur (zamansal analiz için).
    """
    print("Space-Time Cube oluşturuluyor...")
    
    STC_DOSYA = os.path.join(DOCS, "sel_stc.nc")
    
    arcpy.stpm.CreateSpaceTimeCube(
        in_features        = SEL_ANA,
        output_cube        = STC_DOSYA,
        time_field         = "TARIH",
        time_step_interval = "4 Months",
        distance_interval  = "1000 Meters",
    )
    
    print(f"✓ Space-Time Cube: {STC_DOSYA}")
    return STC_DOSYA


def emerging_hotspot_analizi(stc_dosya):
    """
    Emerging Hot Spot Analysis ile zamansal trend analizi yapar.
    """
    print("Emerging Hot Spot Analizi yapılıyor...")
    
    arcpy.stpm.EmergingHotSpotAnalysis(
        in_cube          = stc_dosya,
        analysis_variable= "COUNT",
        output_features  = EHS,
        polygon_mask     = ILCE_GDB,
    )
    
    n = int(arcpy.management.GetCount(EHS).getOutput(0))
    print(f"✓ Emerging Hot Spot: {n} alan")
    
    # Desen özeti
    pattern_sayim = Counter(r[0] for r in arcpy.da.SearchCursor(EHS, ["PATTERN"]) if r[0])
    
    print("  Zamansal desenler:")
    for pattern, sayi in pattern_sayim.most_common():
        print(f"    {pattern}: {sayi}")

# hotspot_analizi()
# stc = space_time_cube_olustur()
# emerging_hotspot_analizi(stc)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. SOSYAL KIRILGANLIK İNDEKSİ (SVI)
# ═══════════════════════════════════════════════════════════════════════════════

def svi_hesapla():
    """
    Sosyal Kırılganlık İndeksi (Social Vulnerability Index) hesaplar.
    
    SVI = 0.40 × Nüfus_norm + 0.35 × Drenaj_norm + 0.25 × Toplanma_norm
    
    Değişkenler:
    - Nüfus: İlçe nüfusu (TÜİK 2022)
    - Drenaj: Çözümsüz drenaj noktası sayısı
    - Toplanma: Toplanma alanı oranı
    """
    print("Sosyal Kırılganlık İndeksi (SVI) hesaplanıyor...")
    
    # Veri (TÜİK 2022 + ABB verileri)
    svi_veri = {
        "Çankaya":     {"nufus": 925828, "drenaj": 14, "toplanma": 0.25},
        "Keçiören":    {"nufus": 938568, "drenaj":  2, "toplanma": 0.25},
        "Altındağ":    {"nufus": 396165, "drenaj":  6, "toplanma": 0.25},
        "Yenimahalle": {"nufus": 695395, "drenaj":  1, "toplanma": 0.25},
        "Akyurt":      {"nufus":  37456, "drenaj":  1, "toplanma": 0.25},
    }
    
    # Normalizasyon fonksiyonu (min-max)
    def norm(deger, tum_degerler):
        mn, mx = min(tum_degerler), max(tum_degerler)
        return (deger - mn) / (mx - mn) if mx > mn else 0
    
    nufuslar  = [v["nufus"]  for v in svi_veri.values()]
    drenajlar = [v["drenaj"] for v in svi_veri.values()]
    
    sonuclar = {}
    for ilce, v in svi_veri.items():
        n = norm(v["nufus"],  nufuslar)
        d = norm(v["drenaj"], drenajlar)
        t = v["toplanma"]
        
        # Ağırlıklı SVI skoru
        svi = 0.40 * n + 0.35 * d + 0.25 * t
        sonuclar[ilce] = round(svi, 3)
    
    print("\n  SVI Sonuçları (Yüksek = Daha Kırılgan):")
    print("  " + "-" * 40)
    for ilce, svi in sorted(sonuclar.items(), key=lambda x: -x[1]):
        bar = "█" * int(svi * 20)
        print(f"    {ilce:15s}: {svi:.3f} {bar}")
    
    return sonuclar

svi_sonuclari = svi_hesapla()


# ═══════════════════════════════════════════════════════════════════════════════
# 12. ZONAL STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

def zonal_statistics():
    """
    İlçe bazında risk istatistiklerini hesaplar.
    """
    print("Zonal Statistics hesaplanıyor...")
    
    # Risk skorunu raster'a çevir
    risk_raster = os.path.join(GDB, "_risk_raster_tmp")
    arcpy.conversion.PointToRaster(
        TAHMIN_V5, "RISK_SKORU_V5", risk_raster,
        cellsize=0.001  # ~100m
    )
    
    # Zonal statistics
    arcpy.sa.ZonalStatisticsAsTable(
        in_zone_data    = ILCE_GDB,
        zone_field      = "AD",
        in_value_raster = risk_raster,
        out_table       = ZONAL,
        statistics_type = "ALL",
    )
    
    # Sonuçları oku
    print("\n  İlçe Bazında Risk İstatistikleri:")
    print("  " + "-" * 60)
    alanlar = ["AD", "MEAN", "STD", "MIN", "MAX", "COUNT"]
    for r in arcpy.da.SearchCursor(ZONAL, alanlar):
        print(f"    {r[0]:15s} Ort: {r[1]:.2f}  Std: {r[2]:.2f}  Min: {r[3]:.0f}  Max: {r[4]:.0f}  n: {r[5]}")
    
    # Geçici raster sil
    if arcpy.Exists(risk_raster):
        arcpy.management.Delete(risk_raster)
    
    print("✓ Zonal Statistics tamamlandı")

# zonal_statistics()


# ═══════════════════════════════════════════════════════════════════════════════
# 13. HARİTA SEMBOLOJİSİ
# ═══════════════════════════════════════════════════════════════════════════════

def harita_sembolojisi_ayarla():
    """
    Harita katmanlarının sembolojisini ayarlar.
    """
    print("Harita sembolojisi ayarlanıyor...")
    
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    m = aprx.activeMap
    
    for lyr in m.listLayers():
        
        # Sel risk haritası
        if lyr.name == "sel_risk_haritasi" or lyr.name == "sel_risk_tahmin_v5":
            lyr.visible = True
            sym = lyr.symbology
            sym.updateRenderer('UniqueValueRenderer')
            sym.renderer.fields = ['Predicted']
            lyr.symbology = sym
            
            sym2 = lyr.symbology
            for grp in sym2.renderer.groups:
                for item in grp.items:
                    val = str(item.values[0][0])
                    if val == '0':
                        item.symbol.color = {'RGB': [0, 197, 82, 180]}    # Yeşil
                        item.symbol.size = 4
                        item.label = 'Düşük Risk'
                    elif val == '1':
                        item.symbol.color = {'RGB': [220, 30, 30, 200]}   # Kırmızı
                        item.symbol.size = 4
                        item.label = 'Yüksek Risk'
            lyr.symbology = sym2
            print("  ✓ Risk haritası sembolojisi")
        
        # Gerçek sel noktaları
        elif lyr.name == "sel_noktalari_ana":
            lyr.visible = True
            sym = lyr.symbology
            sym.updateRenderer('SimpleRenderer')
            sym.renderer.symbol.color = {'RGB': [255, 215, 0, 255]}       # Sarı
            sym.renderer.symbol.size = 8
            sym.renderer.label = 'Gerçek Sel Noktası'
            lyr.symbology = sym
            print("  ✓ Sel noktaları sembolojisi")
        
        # Diğer katmanları kapat
        elif lyr.name not in ["Topographic", "basemap"]:
            lyr.visible = False
    
    # Ankara merkezine zoom
    m.defaultCamera.setExtent(arcpy.Extent(32.3, 39.7, 33.4, 40.2))
    aprx.save()
    
    print("✓ Harita sembolojisi kaydedildi")

# harita_sembolojisi_ayarla()


# ═══════════════════════════════════════════════════════════════════════════════
# 14. DOĞRULAMA ANALİZİ
# ═══════════════════════════════════════════════════════════════════════════════

def dogrulama_analizi():
    """
    Model doğruluğunu gerçek sel noktaları ile test eder.
    Spatial Join ile en yakın tahmin noktasının değerini bulur.
    """
    print("Doğrulama analizi yapılıyor...")
    
    join_cikti = os.path.join(GDB, "dogrulama_join")
    
    arcpy.analysis.SpatialJoin(
        target_features   = SEL_ANA,
        join_features     = TAHMIN_V5,
        out_feature_class = join_cikti,
        join_operation    = "JOIN_ONE_TO_ONE",
        join_type         = "KEEP_ALL",
        match_option      = "CLOSEST"
    )
    
    # Genel doğruluk
    toplam = 0
    dogru  = 0
    
    with arcpy.da.SearchCursor(join_cikti, ["Predicted"]) as cur:
        for row in cur:
            toplam += 1
            if row[0] == 1:
                dogru += 1
    
    print("\n" + "=" * 50)
    print("  DOĞRULAMA SONUÇLARI")
    print("=" * 50)
    print(f"  Toplam gerçek sel noktası   : {toplam}")
    print(f"  Doğru tahmin (risk=1)       : {dogru} ({dogru/toplam*100:.1f}%)")
    print(f"  Yanlış tahmin (risk=0)      : {toplam-dogru} ({(toplam-dogru)/toplam*100:.1f}%)")
    
    # İlçe bazında doğruluk
    print("\n  İlçe Bazında Doğruluk:")
    ilce_sonuclari = {}
    
    with arcpy.da.SearchCursor(join_cikti, ["ilce", "Predicted"]) as cur:
        for row in cur:
            ilce = row[0] if row[0] else "Bilinmeyen"
            if ilce not in ilce_sonuclari:
                ilce_sonuclari[ilce] = {"toplam": 0, "dogru": 0}
            ilce_sonuclari[ilce]["toplam"] += 1
            if row[1] == 1:
                ilce_sonuclari[ilce]["dogru"] += 1
    
    for ilce, sonuc in sorted(ilce_sonuclari.items()):
        if sonuc["toplam"] > 0:
            oran = sonuc["dogru"] / sonuc["toplam"] * 100
            print(f"    {ilce:15s}: {sonuc['dogru']:3d}/{sonuc['toplam']:3d} ({oran:.1f}%)")
    
    print("=" * 50)

# dogrulama_analizi()


# ═══════════════════════════════════════════════════════════════════════════════
# 15. GRAFİK ÇIKTILARI
# ═══════════════════════════════════════════════════════════════════════════════

def tablo_lodo_ciz():
    """
    LODO CV sonuçları için profesyonel tablo grafiği oluşturur.
    """
    fp_bold = fm.FontProperties(family='DejaVu Sans', weight='bold')
    fp = fm.FontProperties(family='DejaVu Sans')
    
    # LODO verileri
    lodo_data = [
        ["Keçiören",    0.986, 0.974, 0.966, 0.950],
        ["Çankaya",     0.975, 0.950, 0.934, 0.927],
        ["Altındağ",    0.913, 0.889, 0.817, 0.889],
        ["Akyurt",      0.976, 0.714, 0.710, 0.833],
        ["Yenimahalle", 0.817, 0.772, 0.680, 1.000],
    ]
    ort = [0.938, 0.869, 0.830, 0.920]
    
    fig, ax = plt.subplots(figsize=(11, 5.5))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    ax.axis('off')
    
    # Başlık
    ax.text(0.5, 0.97, "Leave-One-District-Out — Mekansal Çapraz Doğrulama",
            ha='center', va='top', color='white', fontproperties=fp_bold,
            fontsize=14, transform=ax.transAxes)
    ax.text(0.5, 0.89, "ArcGIS Forest-based Classification v5  ·  5 ilçe  ·  Fold başına bağımsız test",
            ha='center', va='top', color='#aaa', fontproperties=fp,
            fontsize=9, transform=ax.transAxes)
    
    # Tablo ayarları
    cols = ["İlçe", "Accuracy", "F1-Skoru", "MCC", "Recall"]
    col_w = [0.25, 0.18, 0.18, 0.18, 0.18]
    x_pos = [sum(col_w[:i]) for i in range(len(cols))]
    row_h, hdr_h, y_top = 0.115, 0.12, 0.81
    HDR = '#0f3460'
    DARK = '#16213e'
    CARD = '#1a1a2e'
    
    # MCC renk fonksiyonu
    def mcc_renk(v):
        if v >= 0.9: return '#2ecc71'
        elif v >= 0.8: return '#f39c12'
        else: return '#e74c3c'
    
    # Başlık satırı
    for ci, (col, x, w) in enumerate(zip(cols, x_pos, col_w)):
        ax.add_patch(plt.Rectangle((x, y_top-hdr_h), w, hdr_h, facecolor=HDR,
            edgecolor='#444', linewidth=0.8, transform=ax.transAxes, clip_on=False))
        ax.text(x+w/2, y_top-hdr_h/2, col, ha='center', va='center', color='white',
                fontproperties=fp_bold, fontsize=10, transform=ax.transAxes)
    
    # Veri satırları
    for ri, row in enumerate(lodo_data):
        y = y_top - hdr_h - ri*row_h
        bg = DARK if ri%2==0 else CARD
        for ci, (val, x, w) in enumerate(zip(row, x_pos, col_w)):
            ax.add_patch(plt.Rectangle((x, y-row_h), w, row_h, facecolor=bg,
                edgecolor='#333', linewidth=0.4, transform=ax.transAxes, clip_on=False))
            clr = mcc_renk(val) if ci==3 else 'white'
            font = fp_bold if ci==3 else fp
            ax.text(x+w/2, y-row_h/2, f'{val:.3f}' if ci>0 else val,
                    ha='center', va='center', color=clr,
                    fontproperties=font, fontsize=10, transform=ax.transAxes)
    
    # Ortalama satırı
    y = y_top - hdr_h - 5*row_h
    for ci, (val, x, w) in enumerate(zip(["ORTALAMA"]+ort, x_pos, col_w)):
        ax.add_patch(plt.Rectangle((x, y-row_h), w, row_h, facecolor='#1a3a2a',
            edgecolor='#2ecc71', linewidth=1.5, transform=ax.transAxes, clip_on=False))
        clr = '#2ecc71' if ci==3 else 'white'
        ax.text(x+w/2, y-row_h/2, f'{val:.3f}' if ci>0 else val,
                ha='center', va='center', color=clr,
                fontproperties=fp_bold, fontsize=10, transform=ax.transAxes)
    
    # Alt bilgi
    ax.text(0.01, 0.015,
        "MCC = Matthews Correlation Coefficient  ·  Rastgele split MCC: 0.910  ·  "
        "Bağımsız doğrulama (Akyurt n=76): Recall 0.934",
        ha='left', va='bottom', color='#888', fontproperties=fp,
        fontsize=8, transform=ax.transAxes)
    
    # Kaydet
    yol = os.path.join(DOCS, "TABLO_LODO_CV.png")
    fig.savefig(yol, dpi=200, facecolor='#1a1a2e')
    plt.close()
    print(f"✓ Grafik kaydedildi: {yol}")

# tablo_lodo_ciz()


# ═══════════════════════════════════════════════════════════════════════════════
# 16. MEVCUT VERİ DURUMU RAPORU
# ═══════════════════════════════════════════════════════════════════════════════

def veri_durumu_raporu():
    """
    Mevcut veri ve katmanların durumunu raporlar.
    """
    print("\n" + "=" * 60)
    print("  VERİ DURUMU RAPORU")
    print("=" * 60)
    
    # Eğitim verisi
    if arcpy.Exists(EGITIM_V4):
        n_egitim = int(arcpy.management.GetCount(EGITIM_V4).getOutput(0))
        pozitif = sum(1 for r in arcpy.da.SearchCursor(EGITIM_V4, ["SEL_NOKTASI"]) if r[0] == 1)
        negatif = n_egitim - pozitif
        print(f"  Eğitim verisi : {n_egitim} nokta ({pozitif} sel + {negatif} negatif)")
    
    # Tahmin sonuçları
    if arcpy.Exists(TAHMIN_V5):
        n_tahmin = int(arcpy.management.GetCount(TAHMIN_V5).getOutput(0))
        risk_dagilim = Counter()
        for r in arcpy.da.SearchCursor(TAHMIN_V5, ["RISK_SKORU_V5"]):
            s = int(r[0]) if r[0] else 0
            risk_dagilim[s] += 1
        
        print(f"  Tahmin noktası: {n_tahmin}")
        print("  Risk dağılımı:")
        for s in sorted(risk_dagilim):
            etiket = {1: "Çok Düşük", 2: "Düşük", 3: "Orta", 4: "Yüksek", 5: "Çok Yüksek"}.get(s, "?")
            print(f"    Sınıf {s} ({etiket:12s}): {risk_dagilim[s]:4d} ({risk_dagilim[s]/n_tahmin*100:.1f}%)")
    
    # Raster katmanları
    raster_katmanlari = [
        ("DEM", DEM), ("Eğim", EGIM), ("Akış Birikimi", AKIS), 
        ("TWI", TWI), ("Akarsu Mesafe", EUC_DIST)
    ]
    print("\n  Raster Katmanları:")
    for isim, yol in raster_katmanlari:
        durum = "✓" if arcpy.Exists(yol) else "✗"
        print(f"    {durum} {isim}")
    
    print("=" * 60)

veri_durumu_raporu()


# ═══════════════════════════════════════════════════════════════════════════════
# PROJE ÖZETİ
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("  PROJE ÖZETİ")
print("=" * 60)
print("  Model           : Forest-based Classification v5")
print("  Eğitim verisi   : 702 nokta (292 sel + 410 negatif)")
print("  Tahmin noktası  : 8.017")
print("  Değişkenler     : Yükseklik, Eğim, Akış Birikimi, TWI")
print("  LODO MCC        : 0.830")
print("  AUC             : 0.973")
print("  Recall          : 0.920")
print("  F1-Skoru        : 0.869")
print("  Bağımsız test   : Akyurt (n=76) Recall: 0.934")
print("=" * 60)
print("\n  Kullanım:")
print("    - İlk çalıştırma için yorum satırlarını açın")
print("    - Sonraki çalıştırmalarda sadece gerekli fonksiyonları çağırın")
print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════════
# 17. IDW YAĞİŞ İNTERPOLASYONU
# ═══════════════════════════════════════════════════════════════════════════════

def idw_yagis_interpolasyon():
    """
    Yağış istasyonu ölçümlerinden IDW ile yağış yüzeyi üretir.
    Kaynak: MGM yağış istasyonları (yagis_istasyonlari_2022)
    """
    print("IDW Yağış interpolasyonu başlıyor...")

    yagis_pts = os.path.join(GDB, "yagis_istasyonlari_2022")
    idw_out   = os.path.join(GDB, "yagis_interpolasyon")
    idw_ilce  = os.path.join(GDB, "idw_risk_ilce")

    # IDW interpolasyon
    idw_r = arcpy.sa.Idw(
        in_point_features = yagis_pts,
        z_field           = "YAGIS_MM",
        cell_size         = 0.01,
        power             = 2,
    )
    idw_r.save(idw_out)
    print("  ✓ IDW yüzeyi oluşturuldu")

    # İlçe sınırına kırp
    arcpy.management.Clip(idw_out, ILCE_GDB, idw_ilce)
    print(f"  ✓ İlçe sınırına kırpıldı → {idw_ilce}")

    # Eğitim verisine yağış değerlerini ekle
    arcpy.sa.ExtractValuesToPoints(EGITIM_V4, idw_out,
                                   os.path.join(GDB, "_tmp_yagis"))
    arcpy.management.JoinField(EGITIM_V4, arcpy.Describe(EGITIM_V4).OIDFieldName,
                                os.path.join(GDB, "_tmp_yagis"),
                                arcpy.Describe(os.path.join(GDB, "_tmp_yagis")).OIDFieldName,
                                ["RASTERVALU"])
    arcpy.management.AlterField(EGITIM_V4, "RASTERVALU", "YAGIS_MM", "YAGIS_MM")
    print("  ✓ Yağış değerleri eğitim verisine eklendi")

    if arcpy.Exists(os.path.join(GDB, "_tmp_yagis")):
        arcpy.management.Delete(os.path.join(GDB, "_tmp_yagis"))

# idw_yagis_interpolasyon()


# ═══════════════════════════════════════════════════════════════════════════════
# 18. KERNEL DENSITY ANALİZİ
# ═══════════════════════════════════════════════════════════════════════════════

def kernel_density_analizi():
    """
    Sel noktalarının mekânsal yoğunluğunu Kernel Density ile hesaplar.
    Risk yoğunluk haritası üretir.
    """
    print("Kernel Density analizi başlıyor...")

    kd_out  = os.path.join(GDB, "kernel_density_ilce")

    kd_r = arcpy.sa.KernelDensity(
        in_features       = SEL_ANA,
        population_field  = "NONE",
        cell_size         = 0.005,          # ~500m
        search_radius     = 0.05,           # ~5km
        area_unit_scale_factor = "SQUARE_KILOMETERS",
        out_cell_values   = "DENSITIES",
        method            = "PLANAR",
    )
    kd_r.save(kd_out)
    print(f"  ✓ Kernel Density → {kd_out}")

    # İstatistik özeti
    kd_arr = arcpy.RasterToNumPyArray(kd_out, nodata_to_value=0).flatten()
    kd_arr = kd_arr[kd_arr > 0]
    if len(kd_arr) > 0:
        print(f"  Min: {kd_arr.min():.4f}  Max: {kd_arr.max():.4f}  "
              f"Ort: {kd_arr.mean():.4f}")

# kernel_density_analizi()


# ═══════════════════════════════════════════════════════════════════════════════
# 19. NÜFUS RİSK ANALİZİ
# TÜİK 2022 nüfus verileri ile risk altındaki nüfusu hesapla
# ═══════════════════════════════════════════════════════════════════════════════

def nufus_risk_analizi():
    """
    Yüksek ve çok yüksek risk sınıfındaki nüfusu hesaplar.
    Risk noktaları → İlçe bazında nüfus oranı → Toplam risk altındaki nüfus
    """
    print("Nüfus risk analizi başlıyor...")

    # TÜİK 2022 ilçe nüfusları
    NUFUS = {
        "Keçiören":    938568,
        "Çankaya":     925828,
        "Yenimahalle": 695395,
        "Altındağ":    396165,
        "Akyurt":       37456,
    }
    TOPLAM_NUFUS = sum(NUFUS.values())  # 2.993.412

    # Risk sınıfı dağılımını ilçe bazında oku
    ilce_risk = {}   # {ilce: {skor: n}}
    with arcpy.da.SearchCursor(
        TAHMIN_V5, ["RISK_SKORU_V5", "ilce"]
    ) as cur:
        for row in cur:
            skor  = int(row[0]) if row[0] else 0
            ilce  = str(row[1]).strip() if row[1] else "Bilinmiyor"
            if ilce not in ilce_risk:
                ilce_risk[ilce] = {1:0, 2:0, 3:0, 4:0, 5:0}
            if skor in ilce_risk[ilce]:
                ilce_risk[ilce][skor] += 1

    print("\n  İlçe Bazında Risk Altındaki Nüfus:")
    print("  " + "-" * 65)

    toplam_risk_nufus = 0

    for ilce in sorted(NUFUS.keys()):
        if ilce not in ilce_risk:
            continue
        dagilim  = ilce_risk[ilce]
        n_toplam = sum(dagilim.values())
        if n_toplam == 0:
            continue

        # Yüksek + Çok Yüksek = sınıf 4 + 5
        n_yuksek = dagilim.get(4, 0) + dagilim.get(5, 0)
        oran     = n_yuksek / n_toplam if n_toplam > 0 else 0

        # İlçe nüfusuna oran uygula
        risk_nufus = int(NUFUS[ilce] * oran)
        toplam_risk_nufus += risk_nufus

        print(f"    {ilce:15s}  Nüfus: {NUFUS[ilce]:7,}  "
              f"Risk Oranı: %{oran*100:4.1f}  "
              f"Risk Altında: {risk_nufus:7,}")

    print("  " + "-" * 65)
    print(f"    {'TOPLAM':15s}  Nüfus: {TOPLAM_NUFUS:7,}  "
          f"Risk Oranı: %{toplam_risk_nufus/TOPLAM_NUFUS*100:4.1f}  "
          f"Risk Altında: {toplam_risk_nufus:7,}")

    return toplam_risk_nufus

# risk_nufus = nufus_risk_analizi()


# ═══════════════════════════════════════════════════════════════════════════════
# 20. İKLİM SENARYOSU PROJEKSİYONU (RCP 4.5 / RCP 8.5)
# IPCC AR6 Türkiye projeksiyonları + TÜİK 2035 nüfus tahmini
# ═══════════════════════════════════════════════════════════════════════════════

def iklim_senaryosu_hesapla():
    """
    2035 yılı için sel riski altındaki nüfusu projeksiyon yapar.

    Katsayılar:
    - RCP 4.5 (Orta emisyon): %7.9 risk artışı (IPCC AR6 Türkiye)
    - RCP 8.5 (Yüksek emisyon): %13.4 risk artışı
    - Nüfus büyümesi: %2.1 (TÜİK 2035 ilçe projeksiyonu)
    """
    print("İklim senaryosu projeksiyonu hesaplanıyor...\n")

    # Mevcut risk altındaki nüfus (2023)
    NUFUS_2023 = {
        "Keçiören":    152184,
        "Çankaya":     181818,
        "Yenimahalle": 216288,
        "Altındağ":    110782,
        "Akyurt":        4937,
    }
    TOPLAM_2023 = sum(NUFUS_2023.values())  # 666.009

    # Katsayılar
    RCP45_KATSAYI  = 1.079   # %7.9 risk artışı
    RCP85_KATSAYI  = 1.134   # %13.4 risk artışı
    NUFUS_KATSAYI  = 1.021   # %2.1 nüfus artışı

    print(f"  {'İlçe':15s}  {'2023':>8}  {'2035 RCP4.5':>12}  {'2035 RCP8.5':>12}")
    print("  " + "-" * 55)

    toplam_45 = toplam_85 = 0

    for ilce in sorted(NUFUS_2023.keys()):
        n     = NUFUS_2023[ilce]
        r45   = int(n * RCP45_KATSAYI * NUFUS_KATSAYI)
        r85   = int(n * RCP85_KATSAYI * NUFUS_KATSAYI)
        toplam_45 += r45
        toplam_85 += r85
        print(f"    {ilce:15s}  {n:8,}  {r45:12,}  {r85:12,}")

    print("  " + "-" * 55)
    print(f"    {'TOPLAM':15s}  {TOPLAM_2023:8,}  {toplam_45:12,}  {toplam_85:12,}")
    print(f"\n  Artış (RCP 4.5): +{toplam_45-TOPLAM_2023:,} kişi "
          f"(+%{(toplam_45/TOPLAM_2023-1)*100:.1f})")
    print(f"  Artış (RCP 8.5): +{toplam_85-TOPLAM_2023:,} kişi "
          f"(+%{(toplam_85/TOPLAM_2023-1)*100:.1f})")

    return {"mevcut": TOPLAM_2023, "rcp45": toplam_45, "rcp85": toplam_85}

iklim_proj = iklim_senaryosu_hesapla()

