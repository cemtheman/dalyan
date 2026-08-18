import xml.etree.ElementTree as ET
import re
import urllib.request
import numpy as np
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Sessiz Akım — Quiet Current",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Helper function to fetch TCMB EUR Rate online
@st.cache_data(ttl=3600)
def fetch_tcmb_eur():
  try:
    url = "https://www.tcmb.gov.tr/kurlar/today.xml"
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
      xml_data = response.read()
    root = ET.fromstring(xml_data)
    for currency in root.findall("Currency"):
      if currency.attrib.get("CurrencyCode") == "EUR":
        forex_selling = currency.find("ForexSelling").text
        if forex_selling:
          return float(forex_selling), True
  except Exception:
    pass
  return 55.50, False  # Fallback varsayılan değer


# Helper function to fetch Aytemiz Mugla / Ortaca Diesel price online
@st.cache_data(ttl=3600)
def fetch_aytemiz_diesel():
  try:
    url = "https://www.aytemiz.com.tr/akaryakit-fiyatlari/motorin-fiyatlari/mugla-motorin-fiyati"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=8) as response:
      html = response.read().decode("utf-8")

    if "ORTACA" in html.upper():
      part = html.upper().split("ORTACA")[1][:500]
      matches = re.findall(r"(\d{2}[\.,]\d{2})", part)

      if len(matches) >= 2:
        diesel_price = float(matches[1].replace(",", "."))
        return diesel_price, True
      elif len(matches) == 1:
        return float(matches[0].replace(",", ".")), True
  except Exception:
    pass

  return 81.81, False  # Fallback varsayılan motorin değeri


# Header Section
st.markdown(
    '<p style="font-size: 1.8rem; font-weight: 700; color: #1E3A8A;'
    ' margin-bottom: 2px;">⚓ Sessiz Akım — Köyceğiz & Dalyan Elektrikli Filo'
    " Simülasyon Portalı</p>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="font-size: 1.05rem; font-weight: 600; color: #2563EB;'
    ' margin-bottom: 6px;">Quiet Current — Köyceğiz & Dalyan e-Fleet Simulation'
    " Portal</p>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="font-size: 0.88rem; color: #4B5563; margin-bottom: 20px;">Yönetmelik'
    " ve Kurul Kararlarıyla Uyumlu İnteraktif Fizibilite ve Hibe"
    " Simülatörü</p>",
    unsafe_allow_html=True,
)

# Fetch Online Live Data
live_eur, eur_is_live = fetch_tcmb_eur()
live_diesel, diesel_is_live = fetch_aytemiz_diesel()

# Sidebar Controls
with st.sidebar:
  st.header("⚙️ Simülasyon Girdileri")

  st.subheader("🚢 Filo Dönüşüm Hedefleri")
  st.caption("Kooperatif Üyesi Hedefleri (%55 & %70 Hibe)")
  count_v1 = st.number_input(
      "Tip 1 (12m Monohull - 24 Kişi) Adet",
      min_value=0,
      max_value=200,
      value=50,
      step=1,
  )
  count_v2 = st.number_input(
      "Tip 2 (13.5m Katamaran - 32 Kişi) Adet",
      min_value=0,
      max_value=200,
      value=50,
      step=1,
  )
  count_v3 = st.number_input(
      "Tip 3 (14m Katamaran - 54 Kişi) Adet",
      min_value=0,
      max_value=200,
      value=40,
      step=1,
  )

  st.caption("Kooperatif Dışı (Bireysel) Hedefler (%40 Hibe)")
  count_v4_24 = st.number_input(
      "Tip 4A (12m Monohull - 24 Kişi) Adet",
      min_value=0,
      max_value=200,
      value=30,
      step=1,
  )
  count_v4_32 = st.number_input(
      "Tip 4B (13.5m Katamaran - 32 Kişi) Adet",
      min_value=0,
      max_value=200,
      value=20,
      step=1,
  )

  st.divider()

  st.subheader("💶 Tekne Birim Maliyetleri (EUR)")
  st.caption(
      "Tip 4A maliyeti Tip1 ile, Tip 4B maliyeti Tip2 ile aynıdır."
  )
  cost_eur_v1 = st.number_input(
      "Tip 1 & Tip 4A (12m Monohull - 24 Kişi) Maliyeti (€)",
      min_value=10000,
      max_value=1000000,
      value=108100,
      step=1000,
  )
  cost_eur_v2 = st.number_input(
      "Tip 2 & Tip 4B (13.5m Katamaran - 32 Kişi) Maliyeti (€)",
      min_value=10000,
      max_value=1000000,
      value=144140,
      step=1000,
  )
  cost_eur_v3 = st.number_input(
      "Tip 3 (14m Katamaran - 54 Kişi) Maliyeti (€)",
      min_value=10000,
      max_value=1000000,
      value=180180,
      step=1000,
  )

  # Tip 4A ve Tip 4B maliyetleri Tip 1 ve Tip 2'den otomatik türetilir
  cost_eur_v4_24 = cost_eur_v1
  cost_eur_v4_32 = cost_eur_v2

  st.divider()

  st.subheader("🌐 Canlı Piyasa & Kurlar")
  st.caption("TCMB ve Aytemiz servislerinden otomatik güncellenir.")

  eur_rate = st.number_input(
      f"EUR / TRY Kuru {'🟢 Canlı TCMB' if eur_is_live else '🟡 Sabit'}",
      min_value=30.0,
      max_value=120.0,
      value=float(live_eur),
      step=0.1,
  )
  diesel_price = st.number_input(
      (
          "Dizel Yakıt Fiyatı TL/L"
          f" {'🟢 Canlı Aytemiz' if diesel_is_live else '🟡 Sabit'} "
      ),
      min_value=30.0,
      max_value=180.0,
      value=float(live_diesel),
      step=0.1,
  )
  elec_price = st.number_input(
      "Liman Şebeke Elektrik Fiyatı (TL/kWh)",
      min_value=3.0,
      max_value=30.0,
      value=3.50,
      step=0.5,
  )

  st.subheader("İklim ve Operasyon")
  operating_days = st.number_input(
      "Sezon Operasyon Gün Sayısı",
      min_value=30,
      max_value=360,
      value=180,
      step=10,
  )
  sun_hours = st.number_input(
      "Günlük Güneşlenme Süresi (Saat/Gün)",
      min_value=0.0,
      max_value=12.0,
      value=8.0,
      step=0.5,
  )
  daily_miles = st.number_input(
      "Günlük Rota Mesafesi (Mil)",
      min_value=15.0,
      max_value=60.0,
      value=35.0,
      step=5.0,
  )
  cruise_speed = st.number_input(
      "Ortalama Seyir Hızı (Knot)",
      min_value=4.0,
      max_value=10.0,
      value=6.0,
      step=0.5,
  )

# Dynamic Vessel Data Specs Construction
VESSEL_SPECS = {
    "v1": {
        "name": (
            "Tip 1: 12m Monohull (24 Kişi - Kooperatif %55 Hibe - Öncelik 3)"
        ),
        "hull": "monohull",
        "motors": 1,
        "loa": 12.0,
        "beam": 3.8,
        "capacity": 24,
        "merged": 1,
        "disp": 6.5,
        "C": 140,
        "totalCostEur": cost_eur_v1,
        "totalCost": int(cost_eur_v1 * eur_rate),
        "grantRate": 0.55,
        "maxGrant": int(cost_eur_v1 * eur_rate * 0.55),
        "batCapacity": 80,
        "batCostEur": 40000,
        "priority": "Öncelik 3 (%55 Hibe)",
    },
    "v2": {
        "name": (
            "Tip 2: 13.5m Katamaran (32 Kişi - Kooperatif %55 Hibe - Öncelik 2)"
        ),
        "hull": "catamaran",
        "motors": 2,
        "loa": 13.5,
        "beam": 4.2,
        "capacity": 32,
        "merged": 1,
        "disp": 7.8,
        "C": 180,
        "totalCostEur": cost_eur_v2,
        "totalCost": int(cost_eur_v2 * eur_rate),
        "grantRate": 0.55,
        "maxGrant": int(cost_eur_v2 * eur_rate * 0.55),
        "batCapacity": 100,
        "batCostEur": 50000,
        "priority": "Öncelik 2 (%55 Hibe)",
    },
    "v3": {
        "name": (
            "Tip 3: 14m Katamaran (54 Kişi - Kooperatif %70 Hibe - Öncelik 1)"
        ),
        "hull": "catamaran",
        "motors": 2,
        "loa": 14.0,
        "beam": 4.5,
        "capacity": 54,
        "merged": 2,
        "disp": 9.5,
        "C": 210,
        "totalCostEur": cost_eur_v3,
        "totalCost": int(cost_eur_v3 * eur_rate),
        "grantRate": 0.70,
        "maxGrant": int(cost_eur_v3 * eur_rate * 0.70),
        "batCapacity": 140,
        "batCostEur": 70000,
        "priority": "Öncelik 1 (%70 Hibe)",
    },
    "v4_24": {
        "name": (
            "Tip 4A: 12m Monohull (24 Kişi - Kooperatif Dışı %40 Hibe - Öncelik"
            " 4)"
        ),
        "hull": "monohull",
        "motors": 1,
        "loa": 12.0,
        "beam": 3.8,
        "capacity": 24,
        "merged": 1,
        "disp": 6.5,
        "C": 140,
        "totalCostEur": cost_eur_v4_24,
        "totalCost": int(cost_eur_v4_24 * eur_rate),
        "grantRate": 0.40,
        "maxGrant": int(cost_eur_v4_24 * eur_rate * 0.40),
        "batCapacity": 80,
        "batCostEur": 40000,
        "priority": "Öncelik 4 (%40 Hibe)",
    },
    "v4_32": {
        "name": (
            "Tip 4B: 13.5m Katamaran (32 Kişi - Kooperatif Dışı %40 Hibe -"
            " Öncelik 4)"
        ),
        "hull": "catamaran",
        "motors": 2,
        "loa": 13.5,
        "beam": 4.2,
        "capacity": 32,
        "merged": 1,
        "disp": 7.8,
        "C": 180,
        "totalCostEur": cost_eur_v4_32,
        "totalCost": int(cost_eur_v4_32 * eur_rate),
        "grantRate": 0.40,
        "maxGrant": int(cost_eur_v4_32 * eur_rate * 0.40),
        "batCapacity": 100,
        "batCostEur": 50000,
        "priority": "Öncelik 4 (%40 Hibe)",
    },
}


# --- Calibrated Hydrodynamic Function ---
def calc_calibrated_vessel_physics(spec, cruise_spd, d_miles, s_hours):
  payload_weight = spec["capacity"] * 0.080  # Kişi başı 80 kg
  battery_weight = spec["batCapacity"] * 0.010  # LFP Batarya: 10 kg/kWh
  total_disp = spec["disp"] + payload_weight + battery_weight

  if spec["hull"] == "monohull":
    max_power = ((total_disp ** (2 / 3)) * (10**3)) / spec["C"]
    cruise_power = max_power * ((cruise_spd / 10.0) ** 3.3)
  else:
    max_power = ((total_disp**0.72) * (10**3)) / spec["C"]
    cruise_power = max_power * ((cruise_spd / 10.0) ** 2.85)

  cruise_hours = d_miles / cruise_spd
  brut_kwh = cruise_power * cruise_hours

  solar_area = spec["loa"] * spec["beam"] * 0.80
  solar_kwh = solar_area * 0.15 * s_hours
  net_grid_kwh = max(0.0, (brut_kwh / 0.95) - solar_kwh)

  max_diesel_lph = 30.0
  cruise_diesel_lph = (
      max_diesel_lph * ((cruise_spd / 10.0) ** 3.3)
      if spec["hull"] == "monohull"
      else max_diesel_lph * ((cruise_spd / 10.0) ** 2.85)
  )

  return {
      "total_disp": total_disp,
      "payload_weight": payload_weight,
      "battery_weight": battery_weight,
      "max_power": max_power,
      "cruise_power": cruise_power,
      "cruise_hours": cruise_hours,
      "brut_kwh": brut_kwh,
      "solar_area": solar_area,
      "solar_kwh": solar_kwh,
      "net_grid_kwh": net_grid_kwh,
      "cruise_diesel_lph": cruise_diesel_lph,
  }


# --- Fleet Aggregate Calculations ---
counts = {
    "v1": count_v1,
    "v2": count_v2,
    "v3": count_v3,
    "v4_24": count_v4_24,
    "v4_32": count_v4_32,
}

total_vessels = sum(counts.values())
total_capacity = sum(
    counts[k] * VESSEL_SPECS[k]["capacity"] for k in VESSEL_SPECS
)

grants_per_type = {
    k: min(
        VESSEL_SPECS[k]["maxGrant"],
        VESSEL_SPECS[k]["totalCost"] * VESSEL_SPECS[k]["grantRate"],
    )
    for k in VESSEL_SPECS
}

fleet_total_cost = sum(
    counts[k] * VESSEL_SPECS[k]["totalCost"] for k in VESSEL_SPECS
)
fleet_total_grant = sum(counts[k] * grants_per_type[k] for k in VESSEL_SPECS)
fleet_total_capex = fleet_total_cost - fleet_total_grant

# --- Fleet Total CO2 Reduction, Tree Equivalent & Energy Balance Calculation ---
fleet_total_co2_reduction = 0.0
fleet_daily_solar_kwh = 0.0
fleet_daily_grid_kwh = 0.0
fleet_daily_brut_kwh = 0.0

for k, spec_item in VESSEL_SPECS.items():
  if counts[k] > 0:
    p = calc_calibrated_vessel_physics(
        spec_item, cruise_speed, daily_miles, sun_hours
    )

    co2_old = (
        spec_item["merged"]
        * p["cruise_diesel_lph"]
        * p["cruise_hours"]
        * operating_days
        * 2.68
    ) / 1000
    co2_new = (p["net_grid_kwh"] * operating_days * 0.44) / 1000
    single_co2_saved = co2_old - co2_new

    fleet_total_co2_reduction += single_co2_saved * counts[k]
    fleet_daily_solar_kwh += p["solar_kwh"] * counts[k]
    fleet_daily_grid_kwh += p["net_grid_kwh"] * counts[k]
    fleet_daily_brut_kwh += (p["brut_kwh"] / 0.95) * counts[k]

equivalent_trees = int(fleet_total_co2_reduction / 0.022)
fleet_annual_grid_kwh = fleet_daily_grid_kwh * operating_days
fleet_annual_solar_kwh = fleet_daily_solar_kwh * operating_days
solar_coverage_ratio = (
    (fleet_daily_solar_kwh / fleet_daily_brut_kwh) * 100
    if fleet_daily_brut_kwh > 0
    else 0
)

# --- Fleet Summary Dashboard Section ---
st.subheader("🚢 Filo Geneli Toplam Dönüşüm ve Finansman Özeti")
f_kpi1, f_kpi2, f_kpi3, f_kpi4 = st.columns(4)
with f_kpi1:
  st.metric("Hedef Dönüştürülecek Tekne", f"{total_vessels} Adet")
with f_kpi2:
  st.metric("Toplam Filo Yolcu Kapasitesi", f"{total_capacity:,} Kişi")
with f_kpi3:
  st.metric("İhtiyaç Duyulan Toplam Hibe", f"₺{int(fleet_total_grant):,}")
with f_kpi4:
  st.metric("Toplam Net Özkaynak Yatırımı", f"₺{int(fleet_total_capex):,}")

# Fleet Breakdown Table
fleet_summary_df = pd.DataFrame({
    "Tekne Tipi & Kategori": [
        "Tip 1: 12m Monohull (Kooperatif %55)",
        "Tip 2: 13.5m Katamaran (Kooperatif %55)",
        "Tip 3: 14m Katamaran (Kooperatif %70)",
        "Tip 4A: 12m Monohull (Bireysel %40)",
        "Tip 4B: 13.5m Katamaran (Bireysel %40)",
        "TOPLAM",
    ],
    "Adet": [
        count_v1,
        count_v2,
        count_v3,
        count_v4_24,
        count_v4_32,
        total_vessels,
    ],
    "Birim Kapasite": ["24 Kişi", "32 Kişi", "54 Kişi", "24 Kişi", "32 Kişi", "-"],
    "Toplam Kapasite": [
        f"{count_v1 * 24} Kişi",
        f"{count_v2 * 32} Kişi",
        f"{count_v3 * 54} Kişi",
        f"{count_v4_24 * 24} Kişi",
        f"{count_v4_32 * 32} Kişi",
        f"{total_capacity:,} Kişi",
    ],
    "Birim Maliyet (EUR)": [
        f"€{VESSEL_SPECS['v1']['totalCostEur']:,}",
        f"€{VESSEL_SPECS['v2']['totalCostEur']:,}",
        f"€{VESSEL_SPECS['v3']['totalCostEur']:,}",
        f"€{VESSEL_SPECS['v4_24']['totalCostEur']:,}",
        f"€{VESSEL_SPECS['v4_32']['totalCostEur']:,}",
        "-",
    ],
    "Birim Maliyet (TL)": [
        f"₺{VESSEL_SPECS['v1']['totalCost']:,}",
        f"₺{VESSEL_SPECS['v2']['totalCost']:,}",
        f"₺{VESSEL_SPECS['v3']['totalCost']:,}",
        f"₺{VESSEL_SPECS['v4_24']['totalCost']:,}",
        f"₺{VESSEL_SPECS['v4_32']['totalCost']:,}",
        "-",
    ],
    "Brüt Yatırım (TL)": [
        f"₺{count_v1 * VESSEL_SPECS['v1']['totalCost']:,}",
        f"₺{count_v2 * VESSEL_SPECS['v2']['totalCost']:,}",
        f"₺{count_v3 * VESSEL_SPECS['v3']['totalCost']:,}",
        f"₺{count_v4_24 * VESSEL_SPECS['v4_24']['totalCost']:,}",
        f"₺{count_v4_32 * VESSEL_SPECS['v4_32']['totalCost']:,}",
        f"₺{fleet_total_cost:,}",
    ],
    "Toplam Hibe Miktarı": [
        f"₺{int(count_v1 * grants_per_type['v1']):,}",
        f"₺{int(count_v2 * grants_per_type['v2']):,}",
        f"₺{int(count_v3 * grants_per_type['v3']):,}",
        f"₺{int(count_v4_24 * grants_per_type['v4_24']):,}",
        f"₺{int(count_v4_32 * grants_per_type['v4_32']):,}",
        f"₺{int(fleet_total_grant):,}",
    ],
    "Net Özkaynak İhtiyacı": [
        f"₺{int(count_v1 * (VESSEL_SPECS['v1']['totalCost'] - grants_per_type['v1'])):,}",
        f"₺{int(count_v2 * (VESSEL_SPECS['v2']['totalCost'] - grants_per_type['v2'])):,}",
        f"₺{int(count_v3 * (VESSEL_SPECS['v3']['totalCost'] - grants_per_type['v3'])):,}",
        f"₺{int(count_v4_24 * (VESSEL_SPECS['v4_24']['totalCost'] - grants_per_type['v4_24'])):,}",
        f"₺{int(count_v4_32 * (VESSEL_SPECS['v4_32']['totalCost'] - grants_per_type['v4_32'])):,}",
        f"₺{int(fleet_total_capex):,}",
    ],
})
st.table(fleet_summary_df)

# CO2 Reduction & Tree Equivalent Banner
co2_html = f"""
<div style="background-color: #ECFDF5; border: 1.5px solid #10B981; border-radius: 8px; padding: 14px 20px; text-align: center; margin-top: 10px; margin-bottom: 12px;">
    <p style="font-size: 1.25rem; font-weight: 700; color: #065F46; margin: 0;">🌱 Filo Dönüşümü İle Yıllık Toplam CO₂ Salınım Azaltımı: {fleet_total_co2_reduction:,.1f} Ton / Yıl</p>
    <p style="font-size: 1.05rem; font-weight: 600; color: #047857; margin: 4px 0 0 0;">🌳 Bu Çevresel Kazanç Yılda Yaklaşık <b>{equivalent_trees:,} Yetişkin Ağacın</b> Temizlediği Karbon Miktarına Eşdeğerdir.</p>
</div>
"""
st.markdown(co2_html, unsafe_allow_html=True)

# Solar & Grid Electricity Balance Banner
solar_html = f"""
<div style="background-color: #EFF6FF; border: 1.5px solid #3B82F6; border-radius: 8px; padding: 14px 20px; text-align: center; margin-bottom: 20px;">
    <p style="font-size: 1.25rem; font-weight: 700; color: #1E40AF; margin: 0;">⚡ Filo Elektrik ve Şebeke Şarj İhtiyacı Dengesi ({sun_hours} Saat/Gün Güneşlenme)</p>
    <p style="font-size: 1.05rem; font-weight: 600; color: #1D4ED8; margin: 4px 0 0 0;">☀️ Günlük Güneş Üretimi: <b>{fleet_daily_solar_kwh:,.1f} kWh</b> (%{solar_coverage_ratio:.1f} Karşılama) | 🔌 Liman Şebeke Şarj İhtiyacı: <b>{fleet_daily_grid_kwh:,.1f} kWh/gün</b> (Sezonluk: <b>{fleet_annual_grid_kwh:,.0f} kWh/sezon</b>)</p>
</div>
"""
st.markdown(solar_html, unsafe_allow_html=True)

st.divider()

# --- All Vessel Types Detailed Breakdown Section (Alt Alta) ---
st.subheader("📊 Tüm Tekne Tipleri İçin Tekil Detay Analizleri (Kalibre Edilmiş)")

for v_key, spec in VESSEL_SPECS.items():
  with st.expander(f"📌 {spec['name']}", expanded=True):
    p = calc_calibrated_vessel_physics(
        spec, cruise_speed, daily_miles, sun_hours
    )

    motor_multiplier = 1.20 if spec["motors"] == 2 else 1.0
    motor_cost_tl = p["max_power"] * (400 * eur_rate) * motor_multiplier

    per_motor_peak_kw = p["max_power"] / spec["motors"]
    per_motor_cruise_kw = p["cruise_power"] / spec["motors"]

    if spec["motors"] == 2:
      motor_desc = (
          f"• IE5 Çift Sevk Sistemi (2x {per_motor_peak_kw:.1f} kW Zirve Güç)"
      )
      peak_power_str = (
          f"2x {per_motor_peak_kw:.1f} kW ({p['max_power']:.1f} kW Toplam)"
      )
      cruise_power_str = (
          f"2x {per_motor_cruise_kw:.1f} kW ({p['cruise_power']:.1f} kW Toplam)"
      )
    else:
      motor_desc = f"• IE5 Tek Sevk Sistemi ({p['max_power']:.1f} kW Zirve Güç)"
      peak_power_str = f"{p['max_power']:.1f} kW"
      cruise_power_str = f"{p['cruise_power']:.1f} kW"

    solar_cost_tl = p["solar_area"] * (150 * eur_rate)
    bat_cost_tl = spec["batCostEur"] * eur_rate
    infra_share_tl = (750000 * eur_rate) / 150

    hull_cost_tl = spec["totalCost"] - (
        motor_cost_tl + solar_cost_tl + bat_cost_tl + infra_share_tl
    )

    grant_amount = min(spec["maxGrant"], spec["totalCost"] * spec["grantRate"])
    net_capex = spec["totalCost"] - grant_amount

    old_diesel_cost = (
        spec["merged"]
        * (p["cruise_diesel_lph"] * p["cruise_hours"] * operating_days * diesel_price)
    )
    old_maint_cost = spec["merged"] * 140000
    old_total_annual = old_diesel_cost + old_maint_cost

    new_elec_cost = p["net_grid_kwh"] * operating_days * elec_price
    new_degradation = (
        (bat_cost_tl / 3000)
        * (p["brut_kwh"] / spec["batCapacity"])
        * operating_days
    )
    new_maint_cost = old_maint_cost * 0.15
    new_total_annual = new_elec_cost + new_degradation + new_maint_cost

    net_savings = old_total_annual - new_total_annual

    payback_seasons = net_capex / net_savings if net_savings > 0 else float("inf")
    payback_months = (
        payback_seasons * (operating_days / 30.0)
        if net_savings > 0
        else float("inf")
    )

    old_co2 = (
        spec["merged"]
        * p["cruise_diesel_lph"]
        * p["cruise_hours"]
        * operating_days
        * 2.68
    ) / 1000
    new_co2 = (p["net_grid_kwh"] * operating_days * 0.44) / 1000
    net_co2 = old_co2 - new_co2

    # Metric Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
      st.metric("Net Özkaynak CAPEX", f"₺{int(net_capex):,}")
    with kpi2:
      st.metric("Sezonluk Net Tasarruf", f"₺{int(net_savings):,}")
    with kpi3:
      st.metric(
          "Özkaynak Amortisman (ROI)",
          f"{payback_seasons:.1f} Sezon ({int(payback_months)} Ay)",
      )
    with kpi4:
      st.metric("Sezonluk CO2 Salınım Azaltımı", f"{net_co2:.1f} Ton")

    col_left, col_right = st.columns([6, 6])

    with col_left:
      st.markdown("**Yatırım Masrafları (CAPEX) ve Hibe Detayı**")
      capex_df = pd.DataFrame({
          "Maliyet Kalemi": [
              "Brüt Toplam Maliyet",
              "Alınan Devlet Hibesi",
              "Net Özkaynak (CAPEX)",
              "• Tekne Gövde & Genel Donatım Maliyeti",
              motor_desc,
              "• Hardtop Solar PV Tavan",
              "• Lityum Batarya Paketi",
              "• Altyapı Payı (1/150)",
          ],
          "Tutar (TL)": [
              f"₺{spec['totalCost']:,} (€{spec['totalCostEur']:,})",
              f"-₺{int(grant_amount):,}",
              f"₺{int(net_capex):,}",
              f"₺{int(hull_cost_tl):,}",
              f"₺{int(motor_cost_tl):,}",
              f"₺{int(solar_cost_tl):,}",
              f"₺{int(bat_cost_tl):,}",
              f"₺{int(infra_share_tl):,}",
          ],
          "Açıklama": [
              "Birim ihale maliyeti",
              spec["priority"],
              "Yatırımcı Net Sermayesi",
              "Gövde & iç donatım maliyeti",
              (
                  f"{spec['motors']}x Pod/Şaft sevk motoru"
                  f" ({'Çift hattı' if spec['motors']==2 else 'Tek hat'})"
              ),
              f"{p['solar_area']:.1f} m² tavan paneli",
              f"{spec['batCapacity']} kWh LFP paketi",
              "Liman şarj & izleme payı",
          ],
      })
      st.table(capex_df)

    with col_right:
      st.markdown("**Sezonluk İşletme Giderleri (OPEX) ve Tasarruf Dökümü**")
      opex_df = pd.DataFrame({
          "Gider Kalemi": [
              f"Eski Ahşap Yakıt Giderleri ({cruise_speed:.1f} kt /"
              f" {p['cruise_diesel_lph']:.2f} L/h)",
              "Eski Ahşap Sezonluk Bakım/Rektefiye",
              "ESKİ TEKNE SEZONLUK GİDERLER TOPLAMI",
              "Yeni Elektrikli Şebeke Şarj Masrafları",
              "Yeni Batarya Yıpranma Karşılığı",
              "Yeni Elektrikli Periyodik Bakım",
              "YENİ TEKNE SEZONLUK GİDER TOPLAMI",
              "SEZONLUK NET FİNANSAL TASARRUF",
          ],
          "Tutar (TL)": [
              f"₺{int(old_diesel_cost):,}",
              f"₺{int(old_maint_cost):,}",
              f"₺{int(old_total_annual):,}",
              f"₺{int(new_elec_cost):,}",
              f"₺{int(new_degradation):,}",
              f"₺{int(new_maint_cost):,}",
              f"₺{int(new_total_annual):,}",
              f"₺{int(net_savings):,}",
          ],
      })
      st.table(opex_df)

    st.markdown(
        "**⚡ Hidrodinamik ve Sevk Sistemi Kalibrasyonu**"
        f" *(Deplasman: {p['total_disp']:.2f} Ton | Motor Düzeni:"
        f" {spec['motors']}x Sevk Hattı)*"
    )
    tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)
    with tech_col1:
      st.info(f"**10 Knots Zirve Güç:**\n\n{peak_power_str}")
    with tech_col2:
      st.info(
          f"**{cruise_speed:.1f} Knots Seyir Gücü:**\n\n{cruise_power_str} (Dizel:"
          f" {p['cruise_diesel_lph']:.2f} L/h)"
      )
    with tech_col3:
      st.info(
          "**Günlük Solar PV Üretimi:**\n\n"
          f"{p['solar_kwh']:.1f} kWh/gün ({sun_hours}s Güneş)"
      )
    with tech_col4:
      st.info(f"**Net Şebeke Şarj İhtiyacı:**\n\n{p['net_grid_kwh']:.1f} kWh/gün")