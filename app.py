
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import io

st.set_page_config(page_title="Nông Trại Chuyên Nghiệp", layout="wide")

# --- Styles ---
st.markdown("""
<style>
.header {font-size:20px; font-weight:600; color:#145214;}
.sidebar .sidebar-content {padding-top:10px;}
.card {background-color:#ffffff; border-radius:8px; padding:12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);}
</style>
""", unsafe_allow_html=True)

# --- Sample data load ---
DATA_EXCEL = "Nhat_ky_nong_trai.xlsx"

@st.cache_data
def load_data():
    try:
        df = pd.read_excel(DATA_EXCEL, engine='openpyxl')
        df['Ngày'] = pd.to_datetime(df['Ngày']).dt.date
    except Exception as e:
        # create empty
        df = pd.DataFrame(columns=['Ngày','Vườn','Công việc','Nhân công','Ghi chú'])
    return df

df = load_data()

# --- Simple header and sidebar ---
with st.container():
    left, right = st.columns([1,4])
    with left:
        st.markdown("<div class='header'>🌾 NÔNG TRẠI CHUYÊN NGHIỆP</div>", unsafe_allow_html=True)
    with right:
        st.write('')

st.sidebar.title("Vai trò & Chức năng")
role = st.sidebar.selectbox("Chọn vai trò", ['Admin','Quản lý Vườn - Sầu riêng','Quản lý Vườn - Cà phê','Quản lý Vườn - Xoài'])

st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Chọn mục", ['Dashboard','Vườn','Nhật ký công việc','Báo cáo tình trạng cây','Nhắc nhở định kỳ','Tải / Nhập Excel'])

# --- Utility ---
def calc_cost(n):
    return int(n) * 200000

# --- Pages ---
if menu == 'Dashboard':
    st.subheader('Dashboard & Thống kê')
    st.markdown('**Biểu đồ: Chi phí theo ngày từng vườn** (VNĐ)')
    if df.empty:
        st.info('Chưa có dữ liệu. Vui lòng tải file Excel mẫu hoặc thêm nhật ký.')
    else:
        # prepare data for bar chart by day and garden
        chart_data = df.copy()
        chart_data['Chi phí'] = chart_data['Nhân công'].astype(int) * 200000
        # group by date and garden
        grp = chart_data.groupby(['Ngày','Vườn'], as_index=False)['Chi phí'].sum()
        chart = alt.Chart(grp).mark_bar().encode(
            x='Ngày:T',
            y='Chi phí:Q',
            color='Vườn:N',
            tooltip=['Ngày','Vườn','Chi phí']
        ).properties(width=900, height=400)
        st.altair_chart(chart, use_container_width=True)
    
    st.markdown('---')
    st.subheader('Bảng tổng hợp (mới nhất)')
    st.dataframe(df.sort_values('Ngày', ascending=False).reset_index(drop=True))

elif menu == 'Vườn':
    st.subheader('Danh sách vườn')
    gardens = ['Vườn Sầu riêng','Vườn Cà phê','Vườn Xoài']
    st.write('Vườn mẫu:')
    for g in gardens:
        st.markdown(f"- **{g}**")


elif menu == 'Nhật ký công việc':
    st.subheader('Ghi nhật ký công việc (1 lần/ngày)')
    garden_map = {
        'Quản lý Vườn - Sầu riêng': 'Vườn Sầu riêng',
        'Quản lý Vườn - Cà phê': 'Vườn Cà phê',
        'Quản lý Vườn - Xoài': 'Vườn Xoài'
    }
    if role == 'Admin':
        sel_v = st.selectbox('Chọn vườn', ['Vườn Sầu riêng','Vườn Cà phê','Vườn Xoài'])
    else:
        sel_v = garden_map.get(role, 'Vườn Sầu riêng')
    st.markdown(f'**Bạn đang nhập cho:** {sel_v}')
    # auto date
    today = datetime.now().date()
    st.write(f'Ngày báo cáo: **{today}** (tự lưu)')
    task = st.multiselect('Công việc thực hiện', ['Tưới nước','Làm cỏ','Bón phân','Phun thuốc','Thu hoạch','Khác'])
    num_workers = st.number_input('Tổng số nhân công', min_value=0, value=1)
    hours = st.number_input('Số giờ trung bình (tùy chọn)', min_value=0.0, value=8.0)
    note = st.text_input('Ghi chú / Thời tiết (VD: Mưa to - nghỉ nửa ngày)')
    img = st.file_uploader('Ảnh minh chứng (tuỳ chọn)', type=['png','jpg','jpeg'])
    if st.button('Gửi báo cáo'):
        new = {
            'Ngày': today,
            'Vườn': sel_v,
            'Công việc': ', '.join(task) if task else '—',
            'Nhân công': int(num_workers),
            'Ghi chú': note
        }
        df2 = df.append(new, ignore_index=True) if not df.empty else pd.DataFrame([new])
        df2.to_excel(DATA_EXCEL, index=False)
        st.success('Báo cáo đã được lưu! (Bạn có thể tải lại trang để thấy thay đổi)')

elif menu == 'Báo cáo tình trạng cây':
    st.subheader('Báo cáo tình trạng cây (1 lần/ngày)')
    if role == 'Admin':
        sel_v = st.selectbox('Chọn vườn', ['Vườn Sầu riêng','Vườn Cà phê','Vườn Xoài'])
    else:
        garden_map = {
            'Quản lý Vườn - Sầu riêng': 'Vườn Sầu riêng',
            'Quản lý Vườn - Cà phê': 'Vườn Cà phê',
            'Quản lý Vườn - Xoài': 'Vườn Xoài'
        }
        sel_v = garden_map.get(role, 'Vườn Sầu riêng')
    status = st.selectbox('Tình trạng tổng thể', ['Tốt','Bình thường','Có sâu bệnh nhẹ','Cần xử lý'])
    note = st.text_area('Ghi chú chi tiết')
    img = st.file_uploader('Ảnh tình trạng (1-3 ảnh)', accept_multiple_files=True, type=['png','jpg','jpeg'])
    if st.button('Gửi báo cáo tình trạng'):
        # store as a simple excel append to same file for demo (minimal implementation)
        new = {
            'Ngày': datetime.now().date(),
            'Vườn': sel_v,
            'Công việc': f'Báo cáo tình trạng - {status}',
            'Nhân công': 0,
            'Ghi chú': note
        }
        df2 = df.append(new, ignore_index=True) if not df.empty else pd.DataFrame([new])
        df2.to_excel(DATA_EXCEL, index=False)
        st.success('Báo cáo tình trạng đã lưu.')

elif menu == 'Nhắc nhở định kỳ':
    st.subheader('Nhắc nhở định kỳ (Admin quản lý)')
    if role != 'Admin':
        st.info('Chỉ Admin có quyền tạo/điều chỉnh nhắc nhở.')
    else:
        st.write('Tạo nhắc nhở mới (dữ liệu demo, sẽ lưu cục bộ)')
        crop = st.selectbox('Chọn loại cây', ['Sầu riêng','Cà phê','Xoài'])
        content = st.text_input('Nội dung nhắc (VD: Bón phân NPK 16-16-8)')
        period = st.number_input('Chu kỳ (ngày)', min_value=1, value=14)
        start = st.date_input('Ngày bắt đầu')
        if st.button('Tạo nhắc nhở'):
            # naive storage in session state for demo
            reminders = st.session_state.get('reminders', [])
            reminders.append({'Loại cây': crop, 'Nội dung': content, 'Chu kỳ': period, 'Bắt đầu': start.isoformat()})
            st.session_state['reminders'] = reminders
            st.success('Nhắc nhở đã được thêm (lưu tạm trong phiên).')
        if 'reminders' in st.session_state:
            st.table(st.session_state['reminders'])

elif menu == 'Tải / Nhập Excel':
    st.subheader('Tải hoặc nhập dữ liệu "Nhật ký nông trại"')
    st.markdown('Bạn có thể tải file Excel mẫu hoặc upload file Excel để nhập nhiều báo cáo.')
    with st.expander('Tải file mẫu'):
        st.markdown('- File mẫu: **Nhat_ky_nong_trai.xlsx**')
        with open(DATA_EXCEL, 'rb') as f:
            st.download_button('Tải file mẫu', f, file_name='Nhat_ky_nong_trai.xlsx')
    uploaded = st.file_uploader('Upload file Excel (cấu trúc giống mẫu)', type=['xlsx'])
    if uploaded is not None:
        try:
            udf = pd.read_excel(uploaded, engine='openpyxl')
            # simple validation
            required = ['Ngày','Vườn','Công việc','Nhân công','Ghi chú']
            if all([c in udf.columns for c in required]):
                udf['Ngày'] = pd.to_datetime(udf['Ngày']).dt.date
                udf.to_excel(DATA_EXCEL, index=False)
                st.success('Dữ liệu đã được nhập vào hệ thống.')
            else:
                st.error('File không đúng cấu trúc. Vui lòng dùng file mẫu.')
        except Exception as e:
            st.error(f'Không thể đọc file: {e}')
