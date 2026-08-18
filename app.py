import xml.etree.ElementTree as ET
import re
import urllib.request
import numpy as np
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Sessiz Akım — Köyceğiz & Dalyan e-Fleet Simulation Portal",
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


# Vessel Data Specs
VESSEL_SPECS = {
    "v1": {
        "name": "Tip 1: 12m Monohull (24 Kişi - Öncelik 3)",
        "loa": 12.0,
        "beam": 3.8,
        "capacity": 24,
        "merged": 1,
        "disp": 6.5,
        "C": 140,
        "totalCost": 6000000,
        "grantRate": 0.55,
        "maxGrant": 3300000,
        "batCapacity": 80,
        "batCostEur": 40000,
        "priority": "Öncelik 3 (%55 Hibe)",
    },
    "v2": {
        "name": "Tip 2: 13.5m Katamaran (32 Kişi - Öncelik 2)",
        "loa": 13.5,
        "beam": 4.2,
        "capacity": 32,
        "merged": 1,
        "disp": 7.8,
        "C": 180,
        "totalCost": 8000000,
        "grantRate": 0.55,
        "maxGrant": 4400000,
        "batCapacity": 100,
        "batCostEur": 50000,
        "priority": "Öncelik 2 (%55 Hibe)",
    },
    "v3": {
        "name": "Tip 3: 14m Katamaran (54 Kişi - Öncelik 1)",
        "loa": 14.0,
        "beam": 4.5,
        "capacity": 54,
        "merged": 2,
        "disp": 9.5,
        "C": 210,
        "totalCost": 10000000,
        "grantRate": 0.70,
        "maxGrant": 7000000,
        "batCapacity": 140,
        "batCostEur": 70000,
        "priority": "Öncelik 1 (%70 Hibe)",
    },
}

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
  count_v1 = st.number_input(
      "Tip 1 (12m - 24 Kişi) Adet", min_value=0, max_value=200, value=90, step=1
  )
  count_v2 = st.number_input(
      "Tip 2 (13.5m - 32 Kişi) Adet", min_value=0, max_value=200, value=30, step=1
  )
  count_v3 = st.number_input(
      "Tip 3 (14m - 54 Kişi) Adet", min_value=0, max_value=200, value=40, step=1
  )

  st.divider()

  st.subheader("🌐 Canlı Piyasa & Kurlar")
  st.caption("TCMB ve Aytemiz (Ortaca) servislerinden otomatik güncellenir.")

  eur_rate = st.number_input(
      f"EUR / TRY Kuru {'(🟢 Canlı TCMB)' if eur_is_live else '(🟡 Sabit)'}",
      min_value=30.0,
      max_value=120.0,
      value=float(live_eur),
      step=0.1,
  )
  diesel_price = st.number_input(
      (
          "Dizel Yakıt Fiyatı TL/Lt"
          f" {'(🟢 Aytemiz Ortaca)' if diesel_is_live else '(🟡 Sabit)'} "
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
      min_value=90,
      max_value=300,
      value=180,
      step=10,
  )
  sun_hours = st.number_input(
      "Günlük Güneşlenme Süresi (Saat/Gün)",
      min_value=0.0,
      max_value=14.0,
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

# --- Fleet Aggregate Calculations ---
total_vessels = count_v1 + count_v2 + count_v3
total_capacity = (
    count_v1 * VESSEL_SPECS["v1"]["capacity"]
    + count_v2 * VESSEL_SPECS["v2"]["capacity"]
    + count_v3 * VESSEL_SPECS["v3"]["capacity"]
)

v1_grant = min(
    VESSEL_SPECS["v1"]["maxGrant"],
    VESSEL_SPECS["v1"]["totalCost"] * VESSEL_SPECS["v1"]["grantRate"],
)
v2_grant = min(
    VESSEL_SPECS["v2"]["maxGrant"],
    VESSEL_SPECS["v2"]["totalCost"] * VESSEL_SPECS["v2"]["grantRate"],
)
v3_grant = min(
    VESSEL_SPECS["v3"]["maxGrant"],
    VESSEL_SPECS["v3"]["totalCost"] * VESSEL_SPECS["v3"]["grantRate"],
)

fleet_total_cost = (
    count_v1 * VESSEL_SPECS["v1"]["totalCost"]
    + count_v2 * VESSEL_SPECS["v2"]["totalCost"]
    + count_v3 * VESSEL_SPECS["v3"]["totalCost"]
)

fleet_total_grant = (
    count_v1 * v1_grant + count_v2 * v2_grant + count_v3 * v3_grant
)
fleet_total_capex = fleet_total_cost - fleet_total_grant

# --- Fleet Total CO2 Reduction Calculation ---
counts = {"v1": count_v1, "v2": count_v2, "v3": count_v3}
fleet_total_co2_reduction = 0.0

for k, spec_item in VESSEL_SPECS.items():
  if counts[k] > 0:
    s_area = spec_item["loa"] * spec_item["beam"] * 0.80
    p_max = (spec_item["disp"] ** (2 / 3) * (10**3)) / spec_item["C"]
    p_cruise = p_max * ((cruise_speed / 10.0) ** 3)
    c_hrs = daily_miles / cruise_speed
    b_kwh = p_cruise * c_hrs
    s_kwh = s_area * 0.15 * sun_hours
    n_kwh = max(0.0, (b_kwh / 0.95) - s_kwh)
    d_lph = 30.0 * ((cruise_speed / 10.0) ** 3)

    co2_old = (
        spec_item["merged"] * d_lph * c_hrs * operating_days * 2.68
    ) / 1000
    co2_new = (n_kwh * operating_days * 0.44) / 1000
    single_co2_saved = co2_old - co2_new
    fleet_total_co2_reduction += single_co2_saved * counts[k]

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
    "Tekne Tipi": [
        "Tip 1: 12m Monohull (%55 Hibe)",
        "Tip 2: 13.5m Katamaran (%55 Hibe)",
        "Tip 3: 14m Katamaran (%70 Hibe)",
        "TOPLAM",
    ],
    "Adet": [count_v1, count_v2, count_v3, total_vessels],
    "Birim Kapasite": ["24 Kişi", "32 Kişi", "54 Kişi", "-"],
    "Toplam Kapasite": [
        f"{count_v1 * 24} Kişi",
        f"{count_v2 * 32} Kişi",
        f"{count_v3 * 54} Kişi",
        f"{total_capacity:,} Kişi",
    ],
    "Birim Maliyet": [
        f"₺{VESSEL_SPECS['v1']['totalCost']:,}",
        f"₺{VESSEL_SPECS['v2']['totalCost']:,}",
        f"₺{VESSEL_SPECS['v3']['totalCost']:,}",
        "-",
    ],
    "Brüt Yatırım": [
        f"₺{count_v1 * VESSEL_SPECS['v1']['totalCost']:,}",
        f"₺{count_v2 * VESSEL_SPECS['v2']['totalCost']:,}",
        f"₺{count_v3 * VESSEL_SPECS['v3']['totalCost']:,}",
        f"₺{fleet_total_cost:,}",
    ],
    "Toplam Hibe Miktarı": [
        f"₺{int(count_v1 * v1_grant):,}",
        f"₺{int(count_v2 * v2_grant):,}",
        f"₺{int(count_v3 * v3_grant):,}",
        f"₺{int(fleet_total_grant):,}",
    ],
    "Net Özkaynak İhtiyacı": [
        f"₺{int(count_v1 * (VESSEL_SPECS['v1']['totalCost'] - v1_grant)):,}",
        f"₺{int(count_v2 * (VESSEL_SPECS['v2']['totalCost'] - v2_grant)):,}",
        f"₺{int(count_v3 * (VESSEL_SPECS['v3']['totalCost'] - v3_grant)):,}",
        f"₺{int(fleet_total_capex):,}",
    ],
})
st.table(fleet_summary_df)

# Big CO2 Reduction Banner - Single Line
st.markdown(
    '<div style="background-color: #ECFDF5; border: 1.5px solid #10B981;'
    " border-radius: 8px; padding: 12px 20px; text-align: center;"
    ' margin-top: 10px; margin-bottom: 20px;">'
    f'<p style="font-size: 1.35rem; font-weight: 700; color: #065F46; margin:'
    f' 0;">🌱 Filo Dönüşümü İle Yıllık Toplam CO₂ Salınım Azaltımı: {fleet_total_co2_reduction:,.1f} Ton / Yıl</p>'
    "</div>",
    unsafe_allow_html=True,
)

st.divider()

# --- All Vessel Types Detailed Breakdown Section (Alt Alta) ---
st.subheader("📊 Tüm Tekne Tipleri İçin Tekil Detay Analizleri")

for v_key, spec in VESSEL_SPECS.items():
  with st.expander(f"📌 {spec['name']}", expanded=True):
    solar_area = spec["loa"] * spec["beam"] * 0.80
    max_power_kw = (spec["disp"] ** (2 / 3) * (10**3)) / spec["C"]
    cruise_power_kw = max_power_kw * ((cruise_speed / 10.0) ** 3)
    cruise_hours = daily_miles / cruise_speed

    brut_kwh = cruise_power_kw * cruise_hours
    solar_kwh = solar_area * 0.15 * sun_hours
    net_grid_kwh = max(0.0, (brut_kwh / 0.95) - solar_kwh)

    max_diesel_lph = 30.0
    cruise_diesel_lph = max_diesel_lph * ((cruise_speed / 10.0) ** 3)

    motor_cost_tl = max_power_kw * (400 * eur_rate)
    solar_cost_tl = solar_area * (150 * eur_rate)
    bat_cost_tl = spec["batCostEur"] * eur_rate
    infra_share_tl = (750000 * eur_rate) / 150

    grant_amount = min(spec["maxGrant"], spec["totalCost"] * spec["grantRate"])
    net_capex = spec["totalCost"] - grant_amount

    old_diesel_cost = (
        spec["merged"]
        * (cruise_diesel_lph * cruise_hours * operating_days * diesel_price)
    )
    old_maint_cost = spec["merged"] * 140000
    old_total_annual = old_diesel_cost + old_maint_cost

    new_elec_cost = net_grid_kwh * operating_days * elec_price
    new_degradation = (
        (bat_cost_tl / 3000)
        * (brut_kwh / spec["batCapacity"])
        * operating_days
    )
    new_maint_cost = old_maint_cost * 0.15
    new_total_annual = new_elec_cost + new_degradation + new_maint_cost

    net_savings = old_total_annual - new_total_annual
    payback_years = net_capex / net_savings if net_savings > 0 else float("inf")

    old_co2 = (
        spec["merged"]
        * cruise_diesel_lph
        * cruise_hours
        * operating_days
        * 2.68
    ) / 1000
    new_co2 = (net_grid_kwh * operating_days * 0.44) / 1000
    net_co2 = old_co2 - new_co2

    # Metric Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
      st.metric("Net Özkaynak CAPEX", f"₺{int(net_capex):,}")
    with kpi2:
      st.metric("Yıllık Net Tasarruf", f"₺{int(net_savings):,}")
    with kpi3:
      st.metric(
          "Özkaynak Amortisman (ROI)",
          f"{payback_years:.1f} Yıl ({int(payback_years*12)} Ay)",
      )
    with kpi4:
      st.metric("Yıllık CO2 Salınım Azaltımı", f"{net_co2:.1f} Ton")

    col_left, col_right = st.columns([6, 6])

    with col_left:
      st.markdown("**Yatırım Masrafları (CAPEX) ve Hibe Detayı**")
      capex_df = pd.DataFrame({
          "Maliyet Kalemi": [
              "Brüt Toplam Maliyet",
              "Alınan Devlet Hibesi",
              "Net Özkaynak (CAPEX)",
              "• IE5 Elektrikli Sevk Sistemi",
              "• Hardtop Solar PV Tavan",
              "• Lityum Batarya Paketi",
              "• Altyapı Payı (1/150)",
          ],
          "Tutar (TL)": [
              f"₺{spec['totalCost']:,}",
              f"-₺{int(grant_amount):,}",
              f"₺{int(net_capex):,}",
              f"₺{int(motor_cost_tl):,}",
              f"₺{int(solar_cost_tl):,}",
              f"₺{int(bat_cost_tl):,}",
              f"₺{int(infra_share_tl):,}",
          ],
          "Açıklama": [
              "Birim ihale maliyeti",
              spec["priority"],
              "Yatırımcı Net Sermayesi",
              f"{max_power_kw:.1f} kW zirve güç",
              f"{solar_area:.1f} m² tavan paneli",
              f"{spec['batCapacity']} kWh LFP paketi",
              "Liman şarj & izleme payı",
          ],
      })
      st.table(capex_df)

    with col_right:
      st.markdown("**Yıllık İşletme Giderleri (OPEX) ve Tasarruf Dökümü**")
      opex_df = pd.DataFrame({
          "Gider Kalemi": [
              f"Eski Ahşap Yakıt Giderleri ({cruise_speed:.1f} kt /"
              f" {cruise_diesel_lph:.2f} L/h)",
              "Eski Ahşap Yıllık Bakım/Rektefiye",
              "ESKİ TEKNE YILLIK GİDERLER TOPLAMI",
              "Yeni Elektrikli Şebeke Şarj Masrafları",
              "Yeni Batarya Yıpranma Karşılığı",
              "Yeni Elektrikli Periyodik Bakım",
              "YENİ TEKNE YILLIK GİDER TOPLAMI",
              "YILLIK NET FİNANSAL TASARRUF",
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

    st.markdown("**⚡ Hidrodinamik ve Dinamik Enerji Dengesi**")
    tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)
    with tech_col1:
      st.info(f"**10 Knots Zirve Güç:**\n\n{max_power_kw:.1f} kW")
    with tech_col2:
      st.info(
          f"**{cruise_speed:.1f} Knots Seyir Gücü:**\n\n{cruise_power_kw:.1f}"
          f" kW (Dizel: {cruise_diesel_lph:.2f} L/h)"
      )
    with tech_col3:
      st.info(
          "**Günlük Solar PV Üretimi:**\n\n"
          f"{solar_kwh:.1f} kWh/gün ({sun_hours}s Güneş)"
      )
    with tech_col4:
      st.info(f"**Net Şebeke Şarj İhtiyacı:**\n\n{net_grid_kwh:.1f} kWh/gün")