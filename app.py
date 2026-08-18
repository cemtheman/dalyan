import streamlit as st
import pandas as pd
import numpy as np
import urllib.request
import re

# Page Configuration
st.set_page_config(
    page_title="ElectroFleet Maritime — Dalyan Dönüşüm Portalı",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper function to fetch TCMB EUR Rate online
@st.cache_data(ttl=3600)
def fetch_tcmb_eur():
    try:
        url = "https://www.tcmb.gov.tr/kurlar/today.xml"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for currency in root.findall('Currency'):
            if currency.attrib.get('CurrencyCode') == 'EUR':
                forex_selling = currency.find('ForexSelling').text
                if forex_selling:
                    return float(forex_selling), True
    except Exception:
        pass
    return 55.50, False  # Fallback varsayılan değer

# Helper function to fetch Aytemiz Mugla / Ortaca Diesel price online
@st.cache_data(ttl=3600)
def fetch_opet_diesel():
    try:
        url = "https://www.aytemiz.com.tr/akaryakit-fiyatlari/motorin-fiyatlari/mugla-motorin-fiyati"
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode('utf-8')
            
        if "ORTACA" in html.upper():
            # Ortaca kelimesinden sonraki 500 karakterlik tablo bölümünü al
            part = html.upper().split("ORTACA")[1][:500]
            
            # Tüm fiyat desenlerini liste olarak yakala (Örn: ['71.64', '81.95', '81.95'])
            matches = re.findall(r'(\d{2}[\.,]\d{2})', part)
            
            if len(matches) >= 2:
                # 1. Eleman (matches[0]) Benzin, 2. Eleman (matches[1]) Motorin fiyatıdır
                diesel_price = float(matches[1].replace(',', '.'))
                return diesel_price, True
            elif len(matches) == 1:
                return float(matches[0].replace(',', '.')), True
    except Exception:
        pass

    return 81.81, False  # Fallback varsayılan motorin değeri

# Header
st.markdown('<p style="font-size: 1.8rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0px;">⚓ ElectroFleet Maritime — Dalyan Elektrikli Tekne Dönüşüm Portalı</p>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 0.9rem; color: #4B5563; margin-bottom: 20px;">Teknik Komisyon Sonuç Raporu Uyumlu İnteraktif Fizibilite ve Hibe Simülatörü</p>', unsafe_allow_html=True)

# Fetch Online Live Data
live_eur, eur_is_live = fetch_tcmb_eur()
live_diesel, diesel_is_live = fetch_opet_diesel()

# Vessel Data Specs
VESSEL_SPECS = {
    "v1": {
        "name": "Tip 1: 12m Monohull (24 Kişi - Öncelik 3)",
        "loa": 12.0, "beam": 3.8, "capacity": 24, "merged": 1, "disp": 6.5, "C": 140,
        "totalCost": 6000000, "grantRate": 0.55, "maxGrant": 3300000,
        "batCapacity": 80, "batCostEur": 40000, "priority": "Öncelik 3 (%55 Hibe)"
    },
    "v2": {
        "name": "Tip 2: 13.5m Katamaran (32 Kişi - Öncelik 2)",
        "loa": 13.5, "beam": 4.2, "capacity": 32, "merged": 1, "disp": 7.8, "C": 180,
        "totalCost": 8000000, "grantRate": 0.55, "maxGrant": 4400000,
        "batCapacity": 100, "batCostEur": 50000, "priority": "Öncelik 2 (%55 Hibe)"
    },
    "v3": {
        "name": "Tip 3: 14m Katamaran (54 Kişi - Öncelik 1)",
        "loa": 14.0, "beam": 4.5, "capacity": 54, "merged": 2, "disp": 9.5, "C": 210,
        "totalCost": 10000000, "grantRate": 0.70, "maxGrant": 7000000,
        "batCapacity": 140, "batCostEur": 70000, "priority": "Öncelik 1 (%70 Hibe)"
    }
}

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Simülasyon Girdileri")
    
    selected_type = st.selectbox(
        "Tekne Tipi ve Kategori",
        options=list(VESSEL_SPECS.keys()),
        format_func=lambda x: VESSEL_SPECS[x]["name"],
        index=2
    )
    spec = VESSEL_SPECS[selected_type]

    st.subheader("🌐 Canlı Piyasa & Kurlar")
    st.caption("TCMB ve Opet (Ortaca) servislerinden otomatik güncellenir.")
    
    eur_rate = st.number_input(
        f"EUR / TRY Kuru {'(🟢 Canlı)' if eur_is_live else '(🟡 Sabit)'}", 
        min_value=30.0, max_value=120.0, value=float(live_eur), step=0.1
    )
    diesel_price = st.number_input(
        f"Dizel Yakıt Fiyatı {'(🟢 Opet Ortaca)' if diesel_is_live else '(🟡 Sabit)'} TL/L", 
        min_value=30.0, max_value=180.0, value=float(live_diesel), step=0.1
    )
    elec_price = st.number_input("Liman Şebeke Elektrik Fiyatı (TL/kWh)", min_value=3.0, max_value=30.0, value=8.50, step=0.5)

    st.subheader("İklim ve Operasyon")
    operating_days = st.number_input("Sezon Operasyon Gün Sayısı", min_value=90, max_value=300, value=180, step=10)
    sun_hours = st.number_input("Günlük Güneşlenme Süresi (Saat/Gün)", min_value=4.0, max_value=12.0, value=8.0, step=0.5)
    daily_miles = st.number_input("Günlük Rota Mesafesi (Mil)", min_value=15.0, max_value=60.0, value=35.0, step=5.0)
    cruise_speed = st.number_input("Ortalama Seyir Hızı (Knot)", min_value=4.0, max_value=10.0, value=6.0, step=0.5)

# Physics & Hydrodynamics Calculations (Electric Vessel)
solar_area = spec["loa"] * spec["beam"] * 0.80
max_power_kw = (spec["disp"] ** (2/3) * (10 ** 3)) / spec["C"]
cruise_power_kw = max_power_kw * ((cruise_speed / 10.0) ** 3)  # Küp Kuralı
cruise_hours = daily_miles / cruise_speed

brut_kwh = cruise_power_kw * cruise_hours
solar_kwh = solar_area * 0.15 * sun_hours
net_grid_kwh = max(0.0, (brut_kwh / 0.95) - solar_kwh)

# Physics & Dynamic Diesel Calculations (Wooden Vessel)
max_diesel_lph = 30.0
cruise_diesel_lph = max_diesel_lph * ((cruise_speed / 10.0) ** 3)  # Küp Kuralı ile Dinamik Tüketim

# Cost Multipliers
motor_cost_tl = max_power_kw * (400 * eur_rate)
solar_cost_tl = solar_area * (150 * eur_rate)
bat_cost_tl = spec["batCostEur"] * eur_rate
infra_share_tl = (750000 * eur_rate) / 150

# Grants & CAPEX
grant_amount = min(spec["maxGrant"], spec["totalCost"] * spec["grantRate"])
net_capex = spec["totalCost"] - grant_amount

# OPEX Calculations
old_diesel_cost = spec["merged"] * (cruise_diesel_lph * cruise_hours * operating_days * diesel_price)
old_maint_cost = spec["merged"] * 140000
old_total_annual = old_diesel_cost + old_maint_cost

new_elec_cost = net_grid_kwh * operating_days * elec_price
new_degradation = (bat_cost_tl / 3000) * (brut_kwh / spec["batCapacity"]) * operating_days
new_maint_cost = old_maint_cost * 0.15
new_total_annual = new_elec_cost + new_degradation + new_maint_cost

net_savings = old_total_annual - new_total_annual
payback_years = net_capex / net_savings if net_savings > 0 else float('inf')

old_co2 = (spec["merged"] * cruise_diesel_lph * cruise_hours * operating_days * 2.68) / 1000
new_co2 = (net_grid_kwh * operating_days * 0.44) / 1000
net_co2 = old_co2 - new_co2

# Main Dashboard Layout - KPI Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Net Özkaynak CAPEX", f"₺{int(net_capex):,}")
with kpi2:
    st.metric("Yıllık Net Tasarruf", f"₺{int(net_savings):,}")
with kpi3:
    st.metric("Özkaynak Amortisman (ROI)", f"{payback_years:.1f} Yıl ({int(payback_years*12)} Ay)")
with kpi4:
    st.metric("Yıllık CO2 Salınım Azaltımı", f"{net_co2:.1f} Ton")

st.divider()

# Detailed Content Layout
col_left, col_right = st.columns([6, 6])

with col_left:
    st.subheader("📊 Yatırım Masrafları (CAPEX) ve Hibe Detayı")
    capex_df = pd.DataFrame({
        "Maliyet Kalemi": [
            "Brüt Toplam Maliyet", "Alınan Devlet Hibesi", "Net Özkaynak (CAPEX)",
            "• IE5 Elektrikli Sevk Sistemi", "• Hardtop Solar PV Tavan",
            "• Lityum Batarya Paketi", "• Altyapı Payı (1/150)"
        ],
        "Tutar (TL)": [
            f"₺{spec['totalCost']:,}", f"-₺{int(grant_amount):,}", f"₺{int(net_capex):,}",
            f"₺{int(motor_cost_tl):,}", f"₺{int(solar_cost_tl):,}",
            f"₺{int(bat_cost_tl):,}", f"₺{int(infra_share_tl):,}"
        ],
        "Açıklama": [
            "Birim ihale maliyeti", spec["priority"], "Yatırımcı Net Sermayesi",
            f"{max_power_kw:.1f} kW zirve güç", f"{solar_area:.1f} m² tavan paneli",
            f"{spec['batCapacity']} kWh LFP paketi", "Liman şarj & izleme payı"
        ]
    })
    st.table(capex_df)

with col_right:
    st.subheader("💡 Yıllık İşletme Giderleri (OPEX) ve Tasarruf Dökümü")
    opex_df = pd.DataFrame({
        "Gider Kalemi": [
            f"Eski Ahşap Yakıt Giderleri ({cruise_speed:.1f} kt / {cruise_diesel_lph:.2f} L/h)",
            "Eski Ahşap Yıllık Bakım/Rektefiye",
            "ESKİ TEKNE YILLIK GİDERLER TOPLAMI",
            "Yeni Elektrikli Şebeke Şarj Masrafları",
            "Yeni Batarya Yıpranma Karşılığı",
            "Yeni Elektrikli Periyodik Bakım",
            "YENİ TEKNE YILLIK GİDER TOPLAMI",
            "YILLIK NET FİNANSAL TASARRUF"
        ],
        "Tutar (TL)": [
            f"₺{int(old_diesel_cost):,}",
            f"₺{int(old_maint_cost):,}",
            f"₺{int(old_total_annual):,}",
            f"₺{int(new_elec_cost):,}",
            f"₺{int(new_degradation):,}",
            f"₺{int(new_maint_cost):,}",
            f"₺{int(new_total_annual):,}",
            f"₺{int(net_savings):,}"
        ]
    })
    st.table(opex_df)

st.divider()

st.subheader("⚡ Hidrodinamik ve Dinamik Enerji Dengesi Detayları")
tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)
with tech_col1:
    st.info(f"**10 Knots Zirve Güç:**\n\n{max_power_kw:.1f} kW")
with tech_col2:
    st.info(f"**{cruise_speed:.1f} Knots Seyir Gücü:**\n\n{cruise_power_kw:.1f} kW (Dizel: {cruise_diesel_lph:.2f} L/h)")
with tech_col3:
    st.info(f"**Günlük Solar PV Üretimi:**\n\n{solar_kwh:.1f} kWh/gün ({sun_hours}s Güneş)")
with tech_col4:
    st.info(f"**Net Şebeke Şarj İhtiyacı:**\n\n{net_grid_kwh:.1f} kWh/gün")