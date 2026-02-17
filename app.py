import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3
import os
import folium
from folium.plugins import MarkerCluster, Fullscreen
from streamlit_folium import st_folium
import json

# إعداد الصفحة - RTL
st.set_page_config(
    page_title="نظام إدارة العقارات - موريتانيا",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CSS الشامل للتصميم (النسخة الأصلية الكاملة)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    
    /* تطبيق RTL على كل العناصر */
    *, html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif !important;
        direction: rtl !important;
    }
    
    /* الحاوية الرئيسية */
    .main .block-container {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* الشريط الجانبي */
    [data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
        right: 0 !important;
        left: auto !important;
    }
    
    [data-testid="stSidebar"] > div {
        direction: rtl !important;
    }
    
    /* جميع العناصر النصية */
    .stMarkdown, .stText, p, span, label, h1, h2, h3, h4, h5, h6 {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* حقول الإدخال */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* القوائم المنسدلة */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        direction: rtl !important;
        text-align: right !important;
    }
    
    [data-baseweb="select"] {
        direction: rtl !important;
    }
    
    [data-baseweb="select"] > div {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* Radio buttons */
    .stRadio > div {
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stRadio > div > label {
        direction: rtl !important;
        justify-content: flex-end !important;
    }
    
    /* Checkboxes */
    .stCheckbox > label {
        direction: rtl !important;
        flex-direction: row-reverse !important;
    }
    
    /* الأزرار */
    .stButton > button {
        direction: rtl !important;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 30px;
        font-size: 16px;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    /* Headers مخصصة */
    .header-style {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center !important;
        margin-bottom: 30px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    
    .header-style h1, .header-style h3, .header-style p {
        text-align: center !important;
        color: white !important;
    }
    
    /* بطاقات الإحصائيات */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center !important;
        margin: 5px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .metric-card h1, .metric-card h2, .metric-card p {
        text-align: center !important;
        color: white !important;
        margin: 5px 0;
    }
    
    /* بطاقات العقارات */
    .property-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.1);
        margin: 15px 0;
        border-right: 5px solid #2a5298;
        direction: rtl !important;
    }
    
    /* صندوق الموقع */
    .location-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #2a5298;
        margin-bottom: 20px;
        direction: rtl !important;
    }
    
    /* الخريطة */
    .folium-map {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* إخفاء عناصر Streamlit الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* تحسين المظهر العام */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# قاعدة بيانات الولايات والمقاطعات الكاملة
# ==========================================
WILAYA_MOUGHATAA_GPS = {
    "الحوض الشرقي": {
        "center": [16.6167, -7.2500],
        "moughataas": {
            "النعمة": [16.6167, -7.2500], "تمبدغة": [16.2333, -8.1667], "أمرج": [16.5833, -6.9167],
            "باسكنو": [15.8500, -6.7833], "جكني": [16.4167, -6.2667], "ولاتة": [17.3000, -7.0333]
        }
    },
    "الحوض الغربي": {
        "center": [16.5167, -9.9000],
        "moughataas": {
            "لعيون": [16.5167, -9.9000], "كوبني": [15.8167, -9.4167], "تامشكط": [17.2333, -10.6667],
            "الطينطان": [16.9667, -10.1333]
        }
    },
    "لعصابة": {
        "center": [16.6200, -11.4000],
        "moughataas": {
            "كيفه": [16.6200, -11.4000], "باركيول": [16.9833, -12.0500], "بومديد": [17.0333, -11.5167],
            "كرو": [16.2167, -11.3333], "كنكوصة": [15.9333, -11.5167]
        }
    },
    "كوركول": {
        "center": [16.1500, -13.5000],
        "moughataas": {
            "كيهيدي": [16.1500, -13.5000], "امبود": [16.0167, -12.7833], "مقامة": [15.7500, -12.3500],
            "مونكل": [16.5167, -12.8667]
        }
    },
    "لبراكنة": {
        "center": [17.0500, -13.9167],
        "moughataas": {
            "ألاك": [17.0500, -13.9167], "بابابى": [16.8333, -14.4167], "بوكى": [17.0667, -14.6833],
            "امباي": [16.5000, -14.0000], "مقطع لحجار": [17.5167, -14.2167]
        }
    },
    "الترارزة": {
        "center": [16.5139, -15.8050],
        "moughataas": {
            "روصو": [16.5139, -15.8050], "بوتلميت": [17.2500, -14.7000], "كرمسين": [16.6667, -15.4667],
            "المذرذرة": [17.0333, -15.4167], "اركيز": [17.8833, -15.6500], "واد الناقة": [17.6167, -15.5000]
        }
    },
    "آدرار": {
        "center": [20.5167, -13.0500],
        "moughataas": {
            "أطار": [20.5167, -13.0500], "أوجفت": [19.8333, -13.1000], "شنقيط": [20.4667, -12.3500],
            "وادان": [20.9167, -11.6167]
        }
    },
    "داخلت نواذيبو": {
        "center": [20.9333, -17.0333],
        "moughataas": {
            "نواذيبو": [20.9333, -17.0333], "الشامي": [20.3000, -16.0000]
        }
    },
    "تكانت": {
        "center": [18.5500, -11.4167],
        "moughataas": {
            "تجكجة": [18.5500, -11.4167], "المجرية": [19.0667, -12.4667], "تيشيت": [18.4333, -9.5000]
        }
    },
    "كيدي ماغا": {
        "center": [15.1500, -12.1833],
        "moughataas": {
            "سيلبابي": [15.1500, -12.1833], "ولد ينجه": [15.5333, -12.6500], "غابو": [15.2833, -11.9333]
        }
    },
    "تيرس زمور": {
        "center": [22.7333, -12.4833],
        "moughataas": {
            "ازويرات": [22.7333, -12.4833], "افديرك": [22.5833, -12.1167], "بير أم كرين": [23.7167, -14.1333]
        }
    },
    "إينشيري": {
        "center": [19.7500, -14.3833],
        "moughataas": {
            "أكجوجت": [19.7500, -14.3833], "بنشاب": [19.3833, -15.7000]
        }
    },
    "نواكشوط الغربية": {
        "center": [18.0900, -15.9785],
        "moughataas": {
            "تفرغ زينة": [18.1000, -16.0167], "لكصر": [18.0833, -15.9833], "السبخة": [18.0667, -15.9667]
        }
    },
    "نواكشوط الشمالية": {
        "center": [18.1100, -15.9500],
        "moughataas": {
            "تيارت": [18.1333, -15.9167], "دار النعيم": [18.1167, -15.9333], "توجونين": [18.1500, -15.8833]
        }
    },
    "نواكشوط الجنوبية": {
        "center": [18.0700, -15.9600],
        "moughataas": {
            "عرفات": [18.0500, -15.9500], "الميناء": [18.0833, -16.0333], "الرياض": [18.0333, -15.9667]
        }
    }
}

WILAYA_LIST = list(WILAYA_MOUGHATAA_GPS.keys())
WILAYA_MOUGHATAA = {wilaya: list(data["moughataas"].keys()) for wilaya, data in WILAYA_MOUGHATAA_GPS.items()}

# ==========================================
# إعداد قاعدة البيانات (SQLite)
# ==========================================
DB_FILE = 'real_estate_mauritania.db'

def init_db():
    """إنشاء جداول قاعدة البيانات"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY, created_at TEXT, wilaya TEXT, moughataa TEXT, neighborhood TEXT,
            house_number TEXT, latitude REAL, longitude REAL, rooms INTEGER, property_type TEXT,
            status TEXT, amenities TEXT, owner_name TEXT, owner_phone TEXT, owner_id TEXT,
            tenant_name TEXT, tenant_phone TEXT, tenant_id TEXT, rental_date TEXT,
            contract_type TEXT, contract_duration TEXT, monthly_rent REAL, payment_system TEXT,
            arrears REAL DEFAULT 0, deposit REAL, water_status TEXT, electricity_status TEXT, notes TEXT
        )
    ''')
    # جدول المدفوعات
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, property_id TEXT, amount REAL,
            payment_date TEXT, month_covered TEXT, notes TEXT, recorded_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def load_properties_from_db():
    """تحميل العقارات من القاعدة إلى Session State"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM properties")
    rows = c.fetchall()
    # تحويل الصفوف إلى قائمة قواميس
    properties = [dict(row) for row in rows]
    conn.close()
    return properties

def save_property_to_db(prop_data):
    """حفظ عقار جديد"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    columns = ', '.join(prop_data.keys())
    placeholders = ', '.join(['?'] * len(prop_data))
    c.execute(f"INSERT INTO properties ({columns}) VALUES ({placeholders})", list(prop_data.values()))
    conn.commit()
    conn.close()

def delete_property_from_db(prop_id):
    """حذف عقار"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM properties WHERE id = ?", (prop_id,))
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات
init_db()

# تهيئة Session State
if 'properties' not in st.session_state:
    st.session_state.properties = load_properties_from_db()

# ==========================================
# وظائف مساعدة
# ==========================================
def generate_property_id():
    return f"PROP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

def get_coordinates(wilaya, moughataa=None):
    if wilaya in WILAYA_MOUGHATAA_GPS:
        if moughataa and moughataa in WILAYA_MOUGHATAA_GPS[wilaya]["moughataas"]:
            return WILAYA_MOUGHATAA_GPS[wilaya]["moughataas"][moughataa]
        return WILAYA_MOUGHATAA_GPS[wilaya]["center"]
    return [18.0735, -15.9582]

def get_status_color(status):
    colors = {'متاح': 'green', 'مؤجر': 'blue', 'قيد الصيانة': 'orange'}
    return colors.get(status, 'gray')

def get_status_icon(status):
    icons = {'متاح': 'home', 'مؤجر': 'user', 'قيد الصيانة': 'wrench'}
    return icons.get(status, 'info-sign')

def create_map(properties=None, center=None, zoom=6):
    if center is None:
        center = [18.0735, -15.9582]
    
    m = folium.Map(location=center, zoom_start=zoom, tiles='OpenStreetMap')
    Fullscreen(position='topleft', title='شاشة كاملة', title_cancel='خروج').add_to(m)
    
    # طبقة الولايات
    wilaya_group = folium.FeatureGroup(name='🏛️ الولايات')
    for wilaya, data in WILAYA_MOUGHATAA_GPS.items():
        prop_count = len([p for p in (properties or []) if p.get('wilaya') == wilaya])
        popup_html = f"""
        <div style="direction: rtl; text-align: right; font-family: 'Tajawal', sans-serif; min-width: 200px;">
            <h4 style="color: #1e3c72;">🏛️ {wilaya}</h4>
            <p><strong>عدد العقارات:</strong> {prop_count}</p>
        </div>
        """
        folium.Marker(
            location=data['center'], popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"🏛️ {wilaya}",
            icon=folium.Icon(color='darkblue', icon='building', prefix='fa')
        ).add_to(wilaya_group)
    wilaya_group.add_to(m)
    
    # طبقة العقارات
    if properties:
        property_cluster = MarkerCluster(name='🏠 العقارات')
        for prop in properties:
            coords = get_coordinates(prop.get('wilaya'), prop.get('moughataa'))
            # إضافة تباين عشوائي بسيط لتجنب التداخل
            import random
            coords = [coords[0] + random.uniform(-0.01, 0.01), coords[1] + random.uniform(-0.01, 0.01)]
            
            status = prop.get('status', 'متاح')
            color = get_status_color(status)
            icon = get_status_icon(status)
            
            popup_html = f"""
            <div style="direction: rtl; text-align: right; font-family: 'Tajawal', sans-serif; min-width: 250px;">
                <h4 style="color: #1e3c72;">🏠 {prop.get('id')}</h4>
                <p><strong>الحي:</strong> {prop.get('neighborhood')}</p>
                <p><strong>المالك:</strong> {prop.get('owner_name')}</p>
                <p><strong>الحالة:</strong> <span style="color:{color}; font-weight:bold;">{status}</span></p>
                <p><strong>الإيجار:</strong> {prop.get('monthly_rent'):,.0f} أوقية</p>
            </div>
            """
            
            folium.Marker(
                location=coords, popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"🏠 {prop.get('neighborhood')} - {status}",
                icon=folium.Icon(color=color, icon=icon, prefix='fa')
            ).add_to(property_cluster)
        property_cluster.add_to(m)
    
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    return m

# ==========================================
# واجهة المستخدم (الشريط الجانبي)
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: #2a5298; font-size: 60px;'>🏠</h1>
        <h2 style='color: #1e3c72;'>نظام إدارة العقارات</h2>
        <p style='color: #666;'>الجمهورية الإسلامية الموريتانية 🇲🇷</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    menu_options = ["🏠 الرئيسية", "🗺️ الخريطة التفاعلية", "➕ إضافة عقار جديد", "📋 قائمة العقارات", "💰 المدفوعات", "⚙️ الإعدادات"]
    selected_menu = st.radio("القائمة الرئيسية", menu_options, label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### 📈 إحصائيات")
    st.metric("إجمالي العقارات", len(st.session_state.properties))
    if st.session_state.properties:
        rented = len([p for p in st.session_state.properties if p.get('status') == 'مؤجر'])
        st.metric("المؤجرة", rented)

# ==========================================
# الصفحات
# ==========================================

if "الرئيسية" in selected_menu:
    st.markdown("""
    <div class='header-style'>
        <h1>🏠 النظام الذكي الشامل لإدارة العقارات</h1>
        <h3>الجمهورية الإسلامية الموريتانية 🇲🇷</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # بطاقات الإحصائيات
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <h1>🏘️</h1>
            <h2>{len(st.session_state.properties)}</h2>
            <p>إجمالي العقارات</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        rented = len([p for p in st.session_state.properties if p.get('status') == 'مؤجر'])
        st.markdown(f"""
        <div class='metric-card' style='background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);'>
            <h1>✅</h1>
            <h2>{rented}</h2>
            <p>مؤجرة حالياً</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        available = len([p for p in st.session_state.properties if p.get('status') == 'متاح'])
        st.markdown(f"""
        <div class='metric-card' style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);'>
            <h1>🔑</h1>
            <h2>{available}</h2>
            <p>متاحة للإيجار</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        with_arrears = len([p for p in st.session_state.properties if float(p.get('arrears', 0) or 0) > 0])
        st.markdown(f"""
        <div class='metric-card' style='background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);'>
            <h1>⚠️</h1>
            <h2>{with_arrears}</h2>
            <p>متأخرات مالية</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🗺️ نظرة عامة على الخريطة")
    mini_map = create_map(st.session_state.properties, zoom=5)
    st_folium(mini_map, width=None, height=400, returned_objects=[])

# ==========================================
# صفحة إضافة عقار جديد (مصححة بالكامل)
# ==========================================
elif "إضافة عقار" in selected_menu:
    st.markdown("""
    <div class='header-style'>
        <h1>➕ إضافة عقار جديد</h1>
        <p>قم بملء البيانات التالية لتسجيل عقار جديد</p>
    </div>
    """, unsafe_allow_html=True)
    
    # الخطوة 1: تحديد الموقع
    st.markdown("""
    <div class='location-box'>
        <h3>📍 الخطوة 1: تحديد الموقع</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_wilaya = st.selectbox(
            "🏛️ اختر الولاية *",
            options=WILAYA_LIST,
            key="add_wilaya"
        )
    
    with col2:
        # تحديث المقاطعات بناءً على الولاية المختارة
        moughataa_options = WILAYA_MOUGHATAA.get(selected_wilaya, [])
        selected_moughataa = st.selectbox(
            "🏘️ اختر المقاطعة *",
            options=moughataa_options,
            key="add_moughataa"
        )
    
    # عرض الموقع على الخريطة المصغرة
    if selected_wilaya and selected_moughataa:
        st.success(f"✅ الموقع المحدد: **{selected_wilaya}** ← **{selected_moughataa}**")
        coords = get_coordinates(selected_wilaya, selected_moughataa)
        mini_location_map = folium.Map(location=coords, zoom_start=12)
        folium.Marker(location=coords, popup=f"{selected_moughataa}", icon=folium.Icon(color='red', icon='home', prefix='fa')).add_to(mini_location_map)
        st_folium(mini_location_map, width=None, height=200, returned_objects=[])
    
    st.markdown("---")
    
    # الخطوة 2: باقي البيانات
    st.markdown("### 📝 الخطوة 2: إدخال بيانات العقار")
    
    with st.form("property_form", clear_on_submit=True):
        # العنوان التفصيلي
        st.markdown("#### 🏠 العنوان التفصيلي")
        col1, col2 = st.columns(2)
        with col1:
            neighborhood = st.text_input("الحي *", placeholder="أدخل اسم الحي")
        with col2:
            house_number = st.text_input("رقم المنزل", placeholder="مثال: 123")
        
        st.markdown("---")
        
        # مواصفات العقار
        st.markdown("#### 🏗️ مواصفات العقار")
        col1, col2, col3 = st.columns(3)
        with col1:
            rooms = st.selectbox("عدد الغرف *", options=list(range(1, 11)))
        with col2:
            property_type = st.selectbox("تصنيف العقار *", 
                options=["منزل أرضي", "طابق أول", "طابق ثاني", "طابق ثالث", "فيلا", "شقة"])
        with col3:
            status = st.selectbox("الحالة *", options=["متاح", "مؤجر", "قيد الصيانة"])
        
        amenities = st.multiselect("الملحقات والمرافق",
            options=["مطبخ", "حمام داخلي", "صالون", "كراج", "حديقة", "سطح", "مخزن", "بئر", "خزان ماء"])
        
        st.markdown("---")
        
        # بيانات المالك
        st.markdown("#### 👤 بيانات المالك")
        col1, col2, col3 = st.columns(3)
        with col1:
            owner_name = st.text_input("اسم المالك *", placeholder="الاسم الكامل")
        with col2:
            owner_phone = st.text_input("هاتف المالك *", placeholder="مثال: 22123456")
        with col3:
            owner_id = st.text_input("رقم بطاقة التعريف", placeholder="رقم البطاقة")
        
        st.markdown("---")
        
        # بيانات المستأجر
        st.markdown("#### 👥 بيانات المستأجر (إن وجد)")
        col1, col2, col3 = st.columns(3)
        with col1:
            tenant_name = st.text_input("اسم المستأجر", placeholder="الاسم الكامل")
        with col2:
            tenant_phone = st.text_input("هاتف المستأجر", placeholder="مثال: 22123456")
        with col3:
            tenant_id = st.text_input("رقم بطاقة تعريف المستأجر", placeholder="رقم البطاقة")
        
        st.markdown("---")
        
        # الوضعية المالية
        st.markdown("#### 💰 الوضعية المالية")
        col1, col2, col3 = st.columns(3)
        with col1:
            monthly_rent = st.number_input("الإيجار الشهري (أوقية) *", min_value=0, step=1000, value=0)
        with col2:
            payment_system = st.selectbox("نظام التسديد *",
                options=["مقدم (بداية الشهر)", "مؤخر (نهاية الشهر)", "نصف شهري"])
        with col3:
            arrears = st.number_input("المتأخرات (أوقية)", min_value=0, step=1000, value=0)
        
        deposit = st.number_input("مبلغ الضمان (أوقية)", min_value=0, step=1000, value=0)
        
        st.markdown("---")
        notes = st.text_area("📝 ملاحظات إضافية", placeholder="أي معلومات إضافية...")
        
        submitted = st.form_submit_button("💾 حفظ بيانات العقار", use_container_width=True)
        
        if submitted:
            errors = []
            if not neighborhood: errors.append("اسم الحي")
            if not owner_name: errors.append("اسم المالك")
            if not owner_phone: errors.append("رقم هاتف المالك")
            if monthly_rent <= 0: errors.append("الإيجار الشهري")
            
            if errors:
                st.error(f"❌ يرجى ملء الحقول التالية: {', '.join(errors)}")
            else:
                coords = get_coordinates(selected_wilaya, selected_moughataa)
                
                property_data = {
                    'id': generate_property_id(),
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'wilaya': selected_wilaya,
                    'moughataa': selected_moughataa,
                    'neighborhood': neighborhood,
                    'house_number': house_number,
                    'latitude': coords[0],
                    'longitude': coords[1],
                    'rooms': rooms,
                    'property_type': property_type,
                    'status': status,
                    'amenities': ", ".join(amenities) if amenities else "لا يوجد",
                    'owner_name': owner_name,
                    'owner_phone': owner_phone,
                    'owner_id': owner_id,
                    'tenant_name': tenant_name,
                    'tenant_phone': tenant_phone,
                    'tenant_id': tenant_id,
                    'rental_date': str(date.today()),
                    'contract_type': "-", # يمكن إضافتها لاحقاً
                    'contract_duration': "-",
                    'monthly_rent': monthly_rent,
                    'payment_system': payment_system,
                    'arrears': arrears,
                    'deposit': deposit,
                    'water_status': "غير محدد",
                    'electricity_status': "غير محدد",
                    'notes': notes
                }
                
                # حفظ في الذاكرة (Session State)
                st.session_state.properties.append(property_data)
                # حفظ في قاعدة البيانات (SQLite)
                save_property_to_db(property_data)
                
                st.success("✅ تم حفظ بيانات العقار بنجاح في قاعدة البيانات!")
                st.balloons()

# ==========================================
# صفحة قائمة العقارات
# ==========================================
elif "قائمة العقارات" in selected_menu:
    st.markdown("""
    <div class='header-style'>
        <h1>📋 قائمة العقارات المسجلة</h1>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.properties:
        df = pd.DataFrame(st.session_state.properties)
        st.dataframe(df[['id', 'wilaya', 'neighborhood', 'owner_name', 'status', 'monthly_rent']], use_container_width=True)
        
        # تصدير
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل CSV", csv, "data.csv", "text/csv")
    else:
        st.info("لا توجد عقارات مسجلة.")

# ==========================================
# صفحة المدفوعات
# ==========================================
elif "المدفوعات" in selected_menu:
    st.markdown("""
    <div class='header-style'>
        <h1>💰 إدارة المدفوعات</h1>
    </div>
    """, unsafe_allow_html=True)
    
    rented = [p for p in st.session_state.properties if p.get('status') == 'مؤجر']
    if rented:
        with st.form("pay_form"):
            prop_sel = st.selectbox("العقار", options=[f"{p['id']} - {p['neighborhood']}" for p in rented])
            amount = st.number_input("المبلغ", min_value=0.0)
            if st.form_submit_button("تسجيل"):
                pid = prop_sel.split(" - ")[0]
                # تحديث المتأخرات في الذاكرة
                for p in st.session_state.properties:
                    if p['id'] == pid:
                        current = float(p.get('arrears', 0))
                        p['arrears'] = max(0, current - amount)
                        # تحديث في القاعدة
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("UPDATE properties SET arrears = ? WHERE id = ?", (p['arrears'], pid))
                        conn.commit()
                        conn.close()
                        st.success(f"تم الدفع. المتأخرات المتبقية: {p['arrears']}")
                        st.rerun()
    else:
        st.warning("لا توجد عقارات مؤجرة.")

# ==========================================
# صفحة الخريطة
# ==========================================
elif "الخريطة" in selected_menu:
    st.markdown("""
    <div class='header-style'>
        <h1>🗺️ الخريطة التفاعلية</h1>
    </div>
    """, unsafe_allow_html=True)
    m = create_map(st.session_state.properties, zoom=6)
    st_folium(m, width=None, height=600, returned_objects=[])

# ==========================================
# صفحة الإعدادات
# ==========================================
elif "الإعدادات" in selected_menu:
    st.markdown("""
    <div class='header-style'>
        <h1>⚙️ الإعدادات</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.info(f"عدد العقارات في قاعدة البيانات: {len(st.session_state.properties)}")
    
    if st.button("🗑️ حذف جميع البيانات"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM properties")
        conn.commit()
        conn.close()
        st.session_state.properties = []
        st.success("تم الحذف")
        st.rerun()