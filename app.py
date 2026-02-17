import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3
import folium
from folium.plugins import MarkerCluster, Fullscreen
from streamlit_folium import st_folium
import random

# 1. إعداد الصفحة
st.set_page_config(
    page_title="نظام إدارة العقارات - موريتانيا",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. كود CSS لإخفاء الزر وتجميل الواجهة
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    
    /* إخفاء عناصر Streamlit الافتراضية */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header[data-testid="stHeader"] {display: none !important;}
    .stAppDeployButton {display: none !important;}
    
    /* التصميم العام */
    *, html, body, [class*="css"] { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; }
    .main .block-container { direction: rtl !important; text-align: right !important; padding-top: 1rem !important; }
    
    /* الأزرار والبطاقات */
    .stButton > button { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; border-radius: 10px; font-weight: bold; }
    .header-style { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin: 5px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .location-box { background: #f5f7fa; padding: 20px; border-radius: 15px; border: 2px solid #2a5298; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. قاعدة بيانات الولايات والمقاطعات (كاملة)
# ==========================================
WILAYA_MOUGHATAA_GPS = {
    "الحوض الشرقي": {"center": [16.6167, -7.2500], "moughataas": {"النعمة": [16.6167, -7.2500], "تمبدغة": [16.2333, -8.1667], "أمرج": [16.5833, -6.9167], "باسكنو": [15.8500, -6.7833], "جكني": [16.4167, -6.2667], "ولاتة": [17.3000, -7.0333]}},
    "الحوض الغربي": {"center": [16.5167, -9.9000], "moughataas": {"لعيون": [16.5167, -9.9000], "كوبني": [15.8167, -9.4167], "تامشكط": [17.2333, -10.6667], "الطينطان": [16.9667, -10.1333]}},
    "لعصابة": {"center": [16.6200, -11.4000], "moughataas": {"كيفه": [16.6200, -11.4000], "باركيول": [16.9833, -12.0500], "بومديد": [17.0333, -11.5167], "كرو": [16.2167, -11.3333], "كنكوصة": [15.9333, -11.5167]}},
    "كوركول": {"center": [16.1500, -13.5000], "moughataas": {"كيهيدي": [16.1500, -13.5000], "امبود": [16.0167, -12.7833], "مقامة": [15.7500, -12.3500], "مونكل": [16.5167, -12.8667]}},
    "لبراكنة": {"center": [17.0500, -13.9167], "moughataas": {"ألاك": [17.0500, -13.9167], "بابابى": [16.8333, -14.4167], "بوكى": [17.0667, -14.6833], "امباي": [16.5000, -14.0000], "مقطع لحجار": [17.5167, -14.2167]}},
    "الترارزة": {"center": [16.5139, -15.8050], "moughataas": {"روصو": [16.5139, -15.8050], "بوتلميت": [17.2500, -14.7000], "كرمسين": [16.6667, -15.4667], "المذرذرة": [17.0333, -15.4167], "اركيز": [17.8833, -15.6500], "واد الناقة": [17.6167, -15.5000]}},
    "آدرار": {"center": [20.5167, -13.0500], "moughataas": {"أطار": [20.5167, -13.0500], "أوجفت": [19.8333, -13.1000], "شنقيط": [20.4667, -12.3500], "وادان": [20.9167, -11.6167]}},
    "داخلت نواذيبو": {"center": [20.9333, -17.0333], "moughataas": {"نواذيبو": [20.9333, -17.0333], "الشامي": [20.3000, -16.0000]}},
    "تكانت": {"center": [18.5500, -11.4167], "moughataas": {"تجكجة": [18.5500, -11.4167], "المجرية": [19.0667, -12.4667], "تيشيت": [18.4333, -9.5000]}},
    "كيدي ماغا": {"center": [15.1500, -12.1833], "moughataas": {"سيلبابي": [15.1500, -12.1833], "ولد ينجه": [15.5333, -12.6500], "غابو": [15.2833, -11.9333]}},
    "تيرس زمور": {"center": [22.7333, -12.4833], "moughataas": {"ازويرات": [22.7333, -12.4833], "افديرك": [22.5833, -12.1167], "بير أم كرين": [23.7167, -14.1333]}},
    "إينشيري": {"center": [19.7500, -14.3833], "moughataas": {"أكجوجت": [19.7500, -14.3833], "بنشاب": [19.3833, -15.7000]}},
    "نواكشوط الغربية": {"center": [18.0900, -15.9785], "moughataas": {"تفرغ زينة": [18.1000, -16.0167], "لكصر": [18.0833, -15.9833], "السبخة": [18.0667, -15.9667]}},
    "نواكشوط الشمالية": {"center": [18.1100, -15.9500], "moughataas": {"تيارت": [18.1333, -15.9167], "دار النعيم": [18.1167, -15.9333], "توجونين": [18.1500, -15.8833]}},
    "نواكشوط الجنوبية": {"center": [18.0700, -15.9600], "moughataas": {"عرفات": [18.0500, -15.9500], "الميناء": [18.0833, -16.0333], "الرياض": [18.0333, -15.9667]}}
}

WILAYA_LIST = list(WILAYA_MOUGHATAA_GPS.keys())
WILAYA_MOUGHATAA = {wilaya: list(data["moughataas"].keys()) for wilaya, data in WILAYA_MOUGHATAA_GPS.items()}

# ==========================================
# 4. إعداد قاعدة البيانات
# ==========================================
DB_FILE = 'real_estate_v6.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS properties (
        id TEXT PRIMARY KEY, created_at TEXT, wilaya TEXT, moughataa TEXT, neighborhood TEXT,
        house_number TEXT, latitude REAL, longitude REAL, rooms INTEGER, property_type TEXT,
        status TEXT, amenities TEXT, owner_name TEXT, owner_phone TEXT, owner_id TEXT,
        tenant_name TEXT, tenant_phone TEXT, tenant_id TEXT, rental_date TEXT,
        contract_type TEXT, contract_duration TEXT, monthly_rent REAL, payment_system TEXT,
        arrears REAL DEFAULT 0, deposit REAL, water_status TEXT, electricity_status TEXT, notes TEXT
    )''')
    conn.commit()
    conn.close()

def load_properties_from_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM properties")
    rows = c.fetchall()
    properties = [dict(row) for row in rows]
    conn.close()
    return properties

def save_property_to_db(prop_data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    columns = ', '.join(prop_data.keys())
    placeholders = ', '.join(['?'] * len(prop_data))
    c.execute(f"INSERT INTO properties ({columns}) VALUES ({placeholders})", list(prop_data.values()))
    conn.commit()
    conn.close()

init_db()

if 'properties' not in st.session_state:
    st.session_state.properties = load_properties_from_db()

# ==========================================
# 5. وظائف مساعدة
# ==========================================
def generate_property_id():
    return f"PROP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

def get_coordinates(wilaya, moughataa=None):
    if wilaya in WILAYA_MOUGHATAA_GPS:
        if moughataa and moughataa in WILAYA_MOUGHATAA_GPS[wilaya]["moughataas"]:
            return WILAYA_MOUGHATAA_GPS[wilaya]["moughataas"][moughataa]
        return WILAYA_MOUGHATAA_GPS[wilaya]["center"]
    return [18.0735, -15.9582]

def create_map(properties=None, center=None, zoom=6):
    if center is None: center = [18.0735, -15.9582]
    m = folium.Map(location=center, zoom_start=zoom, tiles='OpenStreetMap')
    Fullscreen(position='topleft').add_to(m)
    
    if properties:
        marker_cluster = MarkerCluster(name='العقارات').add_to(m)
        for prop in properties:
            coords = get_coordinates(prop.get('wilaya'), prop.get('moughataa'))
            coords = [coords[0] + random.uniform(-0.01, 0.01), coords[1] + random.uniform(-0.01, 0.01)]
            color = 'green' if prop.get('status') == 'متاح' else 'blue'
            popup_html = f"<div style='direction:rtl;font-family:Tajawal;'><h4>{prop.get('neighborhood')}</h4><p>{prop.get('status')}</p></div>"
            folium.Marker(location=coords, popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=color, icon='home', prefix='fa')).add_to(marker_cluster)
    return m

# ==========================================
# 6. واجهة المستخدم
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='text-align:center;'>🏠 إدارة العقارات</h1>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("القائمة", ["🏠 الرئيسية", "🗺️ الخريطة", "➕ إضافة عقار", "📋 العقارات", "💰 المدفوعات", "⚙️ الإعدادات"], label_visibility="collapsed")
    st.markdown("---")
    st.metric("إجمالي العقارات", len(st.session_state.properties))

# الصفحات
if "الرئيسية" in menu:
    st.markdown("<div class='header-style'><h1>لوحة التحكم</h1></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='metric-card'><h2>{len(st.session_state.properties)}</h2><p>عقارات</p></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><h2>{len([p for p in st.session_state.properties if p.get('status')=='مؤجر'])}</h2><p>مؤجرة</p></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><h2>{len([p for p in st.session_state.properties if float(p.get('arrears',0))>0])}</h2><p>متأخرات</p></div>", unsafe_allow_html=True)
    st.markdown("---")
    st_folium(create_map(st.session_state.properties), width='stretch', height=400, returned_objects=[])

elif "إضافة عقار" in menu:
    st.markdown("<div class='header-style'><h1>➕ إضافة عقار</h1></div>", unsafe_allow_html=True)
    st.markdown("<div class='location-box'><h3>📍 الموقع</h3></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1: wilaya = st.selectbox("الولاية", WILAYA_LIST)
    with col2: moughataa = st.selectbox("المقاطعة", WILAYA_MOUGHATAA.get(wilaya, []))
    
    with st.form("prop_form", clear_on_submit=True):
        neighborhood = st.text_input("الحي *")
        owner_name = st.text_input("اسم المالك *")
        owner_phone = st.text_input("هاتف المالك *")
        monthly_rent = st.number_input("الإيجار", min_value=0, step=1000)
        status = st.selectbox("الحالة", ["متاح", "مؤجر"])
        
        if st.form_submit_button("💾 حفظ", width='stretch'):
            if neighborhood and owner_name:
                coords = get_coordinates(wilaya, moughataa)
                prop_data = {
                    'id': generate_property_id(), 'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'wilaya': wilaya, 'moughataa': moughataa, 'neighborhood': neighborhood,
                    'house_number': '', 'latitude': coords[0], 'longitude': coords[1], 'rooms': 0,
                    'property_type': '', 'status': status, 'amenities': '', 'owner_name': owner_name,
                    'owner_phone': owner_phone, 'owner_id': '', 'tenant_name': '', 'tenant_phone': '',
                    'tenant_id': '', 'rental_date': str(date.today()), 'contract_type': '',
                    'contract_duration': '', 'monthly_rent': monthly_rent, 'payment_system': '',
                    'arrears': 0, 'deposit': 0, 'water_status': '', 'electricity_status': '', 'notes': ''
                }
                st.session_state.properties.append(prop_data)
                save_property_to_db(prop_data)
                st.success("تم الحفظ بنجاح!")
                st.rerun()
            else:
                st.error("املأ الحقول الإلزامية")

elif "العقارات" in menu:
    st.markdown("<div class='header-style'><h1>📋 العقارات</h1></div>", unsafe_allow_html=True)
    if st.session_state.properties:
        df = pd.DataFrame(st.session_state.properties)
        st.dataframe(df[['id', 'wilaya', 'neighborhood', 'owner_name', 'status']], width='stretch')
    else:
        st.info("لا توجد عقارات")

elif "المدفوعات" in menu:
    st.markdown("<div class='header-style'><h1>💰 المدفوعات</h1></div>", unsafe_allow_html=True)
    st.info("قسم المدفوعات")

elif "الخريطة" in menu:
    st.markdown("<div class='header-style'><h1>🗺️ الخريطة</h1></div>", unsafe_allow_html=True)
    st_folium(create_map(st.session_state.properties), width='stretch', height=600, returned_objects=[])

elif "الإعدادات" in menu:
    st.markdown("<div class='header-style'><h1>⚙️ الإعدادات</h1></div>", unsafe_allow_html=True)
    if st.button("🗑️ حذف الكل"):
        conn = sqlite3.connect(DB_FILE)
        conn.cursor().execute("DELETE FROM properties")
        conn.commit()
        conn.close()
        st.session_state.properties = []
        st.rerun()
