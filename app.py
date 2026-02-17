import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sqlite3
import os
import folium
from folium.plugins import MarkerCluster, Fullscreen
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go

# إعداد الصفحة
st.set_page_config(
    page_title="نظام إدارة العقارات - موريتانيا",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS للتصميم (RTL)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    *, html, body, [class*="css"] { font-family: 'Tajawal', sans-serif !important; direction: rtl !important; }
    .main .block-container { direction: rtl !important; text-align: right !important; }
    [data-testid="stSidebar"] { direction: rtl !important; text-align: right !important; right: 0 !important; left: auto !important; }
    .stMarkdown, .stText, p, span, label, h1, h2, h3, h4, h5, h6 { direction: rtl !important; text-align: right !important; }
    .stButton > button { direction: rtl !important; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; border: none; border-radius: 10px; padding: 10px 30px; font-weight: bold; width: 100%; transition: all 0.3s ease; }
    .stButton > button:hover { background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%); transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
    .header-style { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 25px; border-radius: 15px; color: white; text-align: center !important; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; color: white; text-align: center !important; margin: 5px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; color: #1e3c72; }
    /* إخفاء الفوتر */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# إعداد قاعدة البيانات (SQLite)
# ==========================================

DB_FILE = 'real_estate.db'

def init_db():
    """إنشاء جداول قاعدة البيانات إذا لم تكن موجودة"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # جدول العقارات
    c.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            wilaya TEXT,
            moughataa TEXT,
            neighborhood TEXT,
            house_number TEXT,
            latitude REAL,
            longitude REAL,
            rooms INTEGER,
            property_type TEXT,
            status TEXT,
            amenities TEXT,
            owner_name TEXT,
            owner_phone TEXT,
            owner_id TEXT,
            tenant_name TEXT,
            tenant_phone TEXT,
            tenant_id TEXT,
            rental_date TEXT,
            contract_type TEXT,
            contract_duration TEXT,
            monthly_rent REAL,
            payment_system TEXT,
            arrears REAL DEFAULT 0,
            deposit REAL,
            water_status TEXT,
            electricity_status TEXT,
            notes TEXT
        )
    ''')
    
    # جدول المدفوعات (جديد)
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT,
            amount REAL,
            payment_date TEXT,
            month_covered TEXT,
            notes TEXT,
            recorded_at TEXT,
            FOREIGN KEY(property_id) REFERENCES properties(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # للوصول للأعمدة بالأسماء
    return conn

# ==========================================
# البيانات الجغرافية (كاش)
# ==========================================
@st.cache_data
def load_geographic_data():
    # نفس بيانات الولايات السابقة (مختصرة هنا للعرض، يرجى إضافتها كاملة)
    return {
        "الحوض الشرقي": {"center": [16.6167, -7.2500], "moughataas": {"النعمة": [16.6167, -7.2500], "تمبدغة": [16.2333, -8.1667]}} ,
        "نواكشوط الغربية": {"center": [18.0900, -15.9785], "moughataas": {"تفرغ زينة": [18.1000, -16.0167], "لكصر": [18.0833, -15.9833]}},
        # ... يرجى لصق القاموس الكامل WILAYA_MOUGHATAA_GPS هنا كما في الكود السابق ...
        "نواكشوط الشمالية": {"center": [18.1100, -15.9500], "moughataas": {"تيارت": [18.1333, -15.9167], "دار النعيم": [18.1167, -15.9333]}},
        "نواكشوط الجنوبية": {"center": [18.0700, -15.9600], "moughataas": {"عرفات": [18.0500, -15.9500], "الرياض": [18.0333, -15.9667]}}
    }

WILAYA_MOUGHATAA_GPS = load_geographic_data()
WILAYA_LIST = list(WILAYA_MOUGHATAA_GPS.keys())
WILAYA_MOUGHATAA = {w: list(d['moughataas'].keys()) for w, d in WILAYA_MOUGHATAA_GPS.items()}

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

def get_properties_df():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM properties", conn)
    conn.close()
    return df

def get_payments_df():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM payments", conn)
    conn.close()
    return df

# تهيئة قاعدة البيانات عند البدء
init_db()

# ==========================================
# الشريط الجانبي
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #1e3c72;'>🏠 إدارة العقارات</h1>", unsafe_allow_html=True)
    st.markdown("---")
    menu_options = ["🏠 الرئيسية", "🗺️ الخريطة", "➕ إضافة عقار", "💰 المدفوعات", "📋 السجل", "⚙️ الإعدادات"]
    selected_menu = st.radio("القائمة", menu_options, label_visibility="collapsed")
    
    st.markdown("---")
    df_stats = get_properties_df()
    st.metric("إجمالي العقارات", len(df_stats))
    if not df_stats.empty:
        st.metric("المؤجرة", len(df_stats[df_stats['status'] == 'مؤجر']))

# ==========================================
# الصفحات
# ==========================================

if selected_menu == "🏠 الرئيسية":
    st.markdown("<div class='header-style'><h1>لوحة التحكم</h1></div>", unsafe_allow_html=True)
    
    df = get_properties_df()
    
    # مؤشرات رئيسية
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🏘️ العقارات", len(df))
    with c2:
        if not df.empty:
            total_rent = df[df['status'] == 'مؤجر']['monthly_rent'].sum()
            st.metric("💵 الإيجارات الشهرية", f"{total_rent:,.0f} أوقية")
        else:
            st.metric("💵 الإيجارات", "0")
    with c3:
        if not df.empty:
            total_arrears = df['arrears'].sum()
            st.metric("⚠️ المتأخرات", f"{total_arrears:,.0f} أوقية")
        else:
            st.metric("⚠️ المتأخرات", "0")
    with c4:
        # تنبيهات العقود المنتهية (بافتراض مدة سنة من تاريخ البداية)
        alerts = 0
        if not df.empty:
            # منطق التنبيهات يمكن تحسينه
            pass 
        st.metric("🔔 تنبيهات", alerts, delta="عقود قاربت على الانتهاء")
    
    st.markdown("---")
    
    # رسوم بيانية
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 توزيع العقارات حسب الولاية")
            wilaya_counts = df['wilaya'].value_counts().reset_index()
            wilaya_counts.columns = ['الولاية', 'العدد']
            fig = px.pie(wilaya_counts, values='العدد', names='الولاية', title='نسبة العقارات')
            fig.update_layout(font=dict(family="Tajawal"))
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("📈 حالة الإيجار")
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['الحالة', 'العدد']
            fig2 = px.bar(status_counts, x='الحالة', y='العدد', color='الحالة', text_auto=True)
            fig2.update_layout(font=dict(family="Tajawal"))
            st.plotly_chart(fig2, use_container_width=True)
            
        # خريطة مصغرة
        st.subheader("🗺️ نظرة عامة")
        m = folium.Map(location=[18.0735, -15.9582], zoom_start=5)
        marker_cluster = MarkerCluster().add_to(m)
        for _, row in df.iterrows():
            coords = [row['latitude'], row['longitude']]
            folium.Marker(
                location=coords,
                popup=f"{row['neighborhood']} - {row['status']}",
                icon=folium.Icon(color='blue' if row['status'] == 'مؤجر' else 'green', icon='home', prefix='fa')
            ).add_to(marker_cluster)
        st_folium(m, width=None, height=350, returned_objects=[])

    else:
        st.info("لا توجد بيانات لعرضها. قم بإضافة عقار جديد.")

# ==========================================
# صفحة المدفوعات (جديدة)
# ==========================================
elif selected_menu == "💰 المدفوعات":
    st.markdown("<div class='header-style'><h1>سجل المدفوعات المالية</h1></div>", unsafe_allow_html=True)
    
    df_props = get_properties_df()
    rented_props = df_props[df_props['status'] == 'مؤجر']
    
    tab1, tab2 = st.tabs(["تسديد جديد", "سجل المدفوعات"])
    
    with tab1:
        if not rented_props.empty:
            with st.form("payment_form"):
                prop_selection = st.selectbox(
                    "اختر العقار",
                    options=rented_props['id'] + " - " + rented_props['neighborhood']
                )
                prop_id = prop_selection.split(" - ")[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    amount = st.number_input("المبلغ المدفوع (أوقية)", min_value=0.0, step=1000.0)
                with col2:
                    month_covered = st.text_input("الشهر المستحق (مثال: 2024-01)")
                
                notes = st.text_area("ملاحظات")
                
                submitted = st.form_submit_button("تأكيد الدفع")
                
                if submitted:
                    conn = get_db_connection()
                    c = conn.cursor()
                    
                    # إضافة سجل الدفع
                    c.execute('''
                        INSERT INTO payments (property_id, amount, payment_date, month_covered, notes, recorded_at)
                        VALUES (?, ?, date('now'), ?, ?, datetime('now'))
                    ''', (prop_id, amount, month_covered, notes))
                    
                    # تحديث المتأخرات في جدول العقارات
                    # (هنا منطق بسيط: نقص المبلغ من المتأخرات)
                    current_arrears = df_props[df_props['id'] == prop_id]['arrears'].values[0]
                    new_arrears = max(0, current_arrears - amount)
                    
                    c.execute('UPDATE properties SET arrears = ? WHERE id = ?', (new_arrears, prop_id))
                    
                    conn.commit()
                    conn.close()
                    st.success("✅ تم تسجيل الدفع وتحديث المتأخرات!")
                    st.rerun()
        else:
            st.warning("لا توجد عقارات مؤجرة لتسجيل مدفوعاتها.")
            
    with tab2:
        payments_df = get_payments_df()
        if not payments_df.empty:
            st.dataframe(payments_df, use_container_width=True)
        else:
            st.info("لا توجد مدفوعات مسجلة.")

# ==========================================
# صفحة إضافة عقار
# ==========================================
elif selected_menu == "➕ إضافة عقار":
    st.markdown("<div class='header-style'><h1>إضافة عقار جديد</h1></div>", unsafe_allow_html=True)
    
    with st.form("add_property_form"):
        col1, col2 = st.columns(2)
        with col1:
            wilaya = st.selectbox("الولاية", WILAYA_LIST)
        with col2:
            moughataa = st.selectbox("المقاطعة", WILAYA_MOUGHATAA.get(wilaya, []))
        
        neighborhood = st.text_input("الحي *")
        owner_name = st.text_input("اسم المالك *")
        monthly_rent = st.number_input("الإيجار الشهري *", min_value=0.0)
        status = st.selectbox("الحالة", ["متاح", "مؤجر", "قيد الصيانة"])
        
        submitted = st.form_submit_button("حفظ")
        
        if submitted:
            if not neighborhood or not owner_name:
                st.error("يرجى ملء الحقول الإلزامية")
            else:
                coords = get_coordinates(wilaya, moughataa)
                prop_id = generate_property_id()
                
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('''
                    INSERT INTO properties (id, created_at, wilaya, moughataa, neighborhood, owner_name, monthly_rent, status, latitude, longitude)
                    VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (prop_id, wilaya, moughataa, neighborhood, owner_name, monthly_rent, status, coords[0], coords[1]))
                conn.commit()
                conn.close()
                st.success(f"تم حفظ العقار برقم: {prop_id}")
                st.rerun()

# ==========================================
# صفحة السجل
# ==========================================
elif selected_menu == "📋 السجل":
    st.markdown("<div class='header-style'><h1>سجل العقارات</h1></div>", unsafe_allow_html=True)
    df = get_properties_df()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # زر التصدير
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("تحميل CSV", csv, "properties.csv", "text/csv")
    else:
        st.info("السجل فارغ.")

# ==========================================
# صفحة الخريطة والإعدادات (مختصرة)
# ==========================================
elif selected_menu == "🗺️ الخريطة":
    st.markdown("<div class='header-style'><h1>الخريطة التفاعلية</h1></div>", unsafe_allow_html=True)
    df = get_properties_df()
    m = folium.Map(location=[18.0735, -15.9582], zoom_start=6)
    
    # إضافة طبقات...
    st_folium(m, width=None, height=500, returned_objects=[])

elif selected_menu == "⚙️ الإعدادات":
    st.markdown("<div class='header-style'><h1>الإعدادات المتقدمة</h1></div>", unsafe_allow_html=True)
    st.warning("⚠️ هذه الأدوات للتطوير فقط. كن حذراً.")
    
    if st.button("حذف جميع البيانات (إعادة تعيين)"):
        if st.checkbox("أنا متأكد"):
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("DELETE FROM properties")
            c.execute("DELETE FROM payments")
            conn.commit()
            conn.close()
            st.success("تم حذف البيانات.")
            st.rerun()
