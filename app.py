import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(
    page_title="ElectroFleet Maritime — Dalyan Dönüşüm Portalı",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 1.8rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0px; }
    .sub-header { font-size: 0.9rem; color: #4B5563; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">⚓ ElectroFleet Maritime V7 — Dalyan Elektrikli Tekne Dönüşüm Portalı</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Teknik Komisyon Sonuç Raporu Uyumlu İnteraktif Fizibilite ve Hibe Simülatörü</p>', unsafe_allow_html=True)

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

    st.subheader("İklim ve Operasyon")
    operating_days = st.number_input("Sezon Operasyon Gün Sayısı", min_value=90, max_value=300, value=180, step=10)
    sun_hours = st.number_input("Günlük Güneşlenme Süresi (Saat/Gün)", min_value=4.0, max_value=12.0, value=8.0, step=0.5)
    daily_miles = st.number_input("Günlük Rota Mesafesi (Mil)", min_value=15.0, max_value=60.0, value=35.0, step=5.0)

    st.subheader("Finansal ve Piyasa Verileri")
    eur_rate = st.number_input("EUR / TRY Kuru (TCMB)", min_value=30.0, max_value=100.0, value=55.50, step=0.5)
    diesel_price = st.number_input("Dizel Yakıt Fiyatı (TL/Litre - PO)", min_value=30.0, max_value=150.0, value=81.0, step=1.0)
    elec_price = st.number_input("Liman Şebeke Elektrik Fiyatı (TL/kWh)", min_value=3.0, max_value=25.0, value=8.50, step=0.5)

# Physics & Power Calculations
solar_area = spec["loa"] * spec["beam"] * 0.80
max_power_kw = (spec["disp"] ** (2/3) * (10 ** 3)) / spec["C"]
cruise_power_kw = max_power_kw * ((6.0 / 10.0) ** 3)
cruise_hours = daily_miles / 6.0

brut_kwh = cruise_power_kw * cruise_hours
solar_kwh = solar_area * 0.15 * sun_hours
net_grid_kwh = max(0.0, (brut_kwh / 0.95) - solar_kwh)

# Cost Multipliers
motor_cost_tl = max_power_kw * (400 * eur_rate)
solar_cost_tl = solar_area * (150 * eur_rate)
bat_cost_tl = spec["batCostEur"] * eur_rate
infra_share_tl = (750000 * eur_rate) / 150

# Grants & CAPEX
grant_amount = min(spec["maxGrant"], spec["totalCost"] * spec["grantRate"])
net_capex = spec["totalCost"] - grant_amount

# OPEX Calculations
old_diesel_cost = spec["merged"] * (14.5 * cruise_hours * operating_days * diesel_price)
old_maint_cost = spec["merged"] * 140000
old_total_annual = old_diesel_cost + old_maint_cost

new_elec_cost = net_grid_kwh * operating_days * elec_price
new_degradation = (bat_cost_tl / 3000) * (brut_kwh / spec["batCapacity"]) * operating_days
new_maint_cost = old_maint_cost * 0.15
new_total_annual = new_elec_cost + new_degradation + new_maint_cost

net_savings = old_total_annual - new_total_annual
payback_years = net_capex / net_savings if net_savings > 0 else float('inf')

old_co2 = (spec["merged"] * 14.5 * cruise_hours * operating_days * 2.68) / 1000
new_co2 = (net_grid_kwh * operating_days * 0.44) / 1000
net_co2 = old_co2 - new_co2

# Main Dashboard Layout
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

# Detailed Tables & Charts
col_left, col_right = st.columns([6, 6])

with col_left:
    st.subheader("📊 CAPEX ve Hibe Detayı")
    capex_df = pd.DataFrame({
        "Maliyet Kalemi": [
            "Brüt Toplam Maliyet", "Alınan Devlet Hibesi", "NET ÖZKAYNAK CAPEX",
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

    st.subheader("⚡ Teknik ve Enerji Dengesi")
    st.write(f"- **10 Knots Zirve Güç:** {max_power_kw:.1f} kW")
    st.write(f"- **6 Knots Seyir Gücü:** {cruise_power_kw:.1f} kW")
    st.write(f"- **Günlük Solar PV Üretimi ({sun_hours}s Güneş):** {solar_kwh:.1f} kWh/gün")
    st.write(f"- **Faturaya Yansıyan Net Şebeke Şarjı:** {net_grid_kwh:.1f} kWh/gün")

with col_right:
    st.subheader("📈 10 Yıllık Kümülatif Maliyet Grafiği")
    years = list(range(11))
    old_costs = [y * old_total_annual for y in years]
    new_costs = [net_capex + (y * new_total_annual) for y in years]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=old_costs, name="Eski Ahşap Tekne", marker_color="#94A3B8"))
    fig.add_trace(go.Bar(x=years, y=new_costs, name="Yeni Elektrikli Tekne", marker_color="#1E3A8A"))
    fig.update_layout(
        barmode='group',
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("💡 OPEX Yıllık Harcama Kıyaslaması")
    st.write(f"- **Eski Ahşap Tekne Yıllık Gider:** ₺{int(old_total_annual):,} (Dizel + Bakım)")
    st.write(f"- **Yeni Elektrikli Tekne Yıllık Gider:** ₺{int(new_total_annual):,} (Şarj + Yıpranma + Bakım)")
    st.write(f"- **Yıllık Net Finansal Tasarruf:** ₺{int(net_savings):,}")
