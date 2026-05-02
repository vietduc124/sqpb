import base64
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", override=True)


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()

logo_path = Path(__file__).parent.parent / "assets" / "logo.jpg"
logo_html = '<div style="width:90px;height:90px;"></div>'
if logo_path.exists():
    b64 = _b64(logo_path)
    logo_html = f'<a href="/" target="_self"><img src="data:image/jpeg;base64,{b64}" style="height:90px;width:90px;object-fit:contain;cursor:pointer;" alt="Logo"/></a>'

sch_path = Path(__file__).parent.parent / "assets" / "SCH.jpg"
sch_html = '<div style="background:#e0d0a0;border-radius:10px;padding:40px;text-align:center;color:#8b6914;font-weight:600">Ảnh trường</div>'
if sch_path.exists():
    b64 = _b64(sch_path)
    sch_html = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,.15);border:3px solid #e0d0a0;display:block;" alt="Trường Sĩ Quan Pháo Binh"/>'

st.markdown(f"""
<style>
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {{ display:none !important; }}
#MainMenu, footer, header {{ visibility:hidden; }}

.stApp {{ background:#f5edd8; }}
html,body,.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section.main,
.main .block-container,.block-container {{
    padding:0 !important; margin:0 !important;
    max-width:100% !important; width:100% !important;
    overflow-x:hidden !important;
}}

.pb-header {{
    display:flex; align-items:center; gap:24px;
    background:#fff; padding:14px 40px;
    border-bottom:2px solid #e0d0a0;
    box-shadow:0 2px 8px rgba(0,0,0,.06);
}}
.pb-title {{ flex:1; text-align:center; line-height:1.3; }}
.pb-title-1 {{ font-size:20px; font-weight:700; color:#1a5c1a; text-transform:uppercase; letter-spacing:1px; }}
.pb-title-2 {{ font-size:30px; font-weight:900; color:#c0392b; text-transform:uppercase; letter-spacing:2px; }}

.pb-nav-btn {{
    display:inline-block; text-decoration:none;
    background:#1a2e5a; color:#ffd700 !important;
    border:2px solid #ffd700; border-radius:6px;
    padding:7px 16px; font-size:13px; font-weight:700;
    white-space:nowrap;
}}

.pb-ticker {{
    background:#1a2e5a; padding:12px 20px; text-align:center;
}}
.pb-ticker-inner {{
    color:#ffd700; font-weight:700; font-size:15px; line-height:1.7;
}}

.tg-wrap {{
    display:flex; gap:32px; align-items:flex-start;
    max-width:960px; margin:32px auto; padding:0 24px;
    box-sizing:border-box;
}}
.tg-left {{ flex:0 0 400px; max-width:400px; }}
.tg-right {{ flex:1; min-width:0; }}

@media(max-width:768px){{
    .pb-header{{ padding:10px 16px; gap:12px; }}
    .pb-header img{{ height:60px !important; width:60px !important; }}
    .pb-title-1{{ font-size:13px; }}
    .pb-title-2{{ font-size:18px; }}
    .pb-nav-btn{{ font-size:11px; padding:5px 10px; }}
    .tg-wrap{{ flex-direction:column; gap:20px; margin:20px auto; padding:0 16px; }}
    .tg-left{{ flex:none; max-width:100%; width:100%; }}
}}
@media(max-width:480px){{
    .pb-title-1{{ font-size:11px; }}
    .pb-title-2{{ font-size:15px; }}
    .pb-header img{{ height:48px !important; width:48px !important; }}
}}
</style>

<div class="pb-header">
    {logo_html}
    <div class="pb-title">
        <div class="pb-title-1">Bộ Tư Lệnh Pháo Binh - Tên Lửa</div>
        <div class="pb-title-2">Trường Sĩ Quan Pháo Binh</div>
    </div>
    <a class="pb-nav-btn" href="/" target="_self">💬 Hỏi đáp</a>
</div>

<div class="pb-ticker">
    <span class="pb-ticker-inner">
        BÀI DỰ THI TÌM HIỂU 80 NĂM NGÀY TRUYỀN THỐNG BỘ ĐỘI PHÁO BINH - TÊN LỬA<br>
        QUÂN ĐỘI NHÂN DÂN VIỆT NAM<br>
        (1946 - 2026)
    </span>
</div>

<div class="tg-wrap">
    <div class="tg-left">
        {sch_html}
    </div>
    <div class="tg-right">
        <h3 style="color:#1a2e5a;margin:0 0 16px;font-size:20px;text-transform:uppercase;letter-spacing:1px">NHÓM TÁC GIẢ</h3>
        <p style="margin:0 0 8px"><strong>Trưởng nhóm:</strong> Thiếu tá Lê Thị Phương Thanh</p>
        <p style="margin:0 0 6px"><strong>Thành viên:</strong></p>
        <ul style="margin:0 0 16px;padding-left:20px;line-height:2">
            <li>Trung tá Dương Thị Kiều Tú</li>
            <li>Thiếu tá Vũ Thị Thin</li>
            <li>Đại úy Nguyễn Hoàng An</li>
            <li>Trung úy Nguyễn Thị Hảo</li>
        </ul>
        <hr style="border:none;border-top:1px solid #e0d0a0;margin:12px 0"/>
        <p style="margin:0"><strong>Đơn vị:</strong> Khoa Khoa Học Cơ Bản – Trường Sĩ Quan Pháo Binh</p>
    </div>
</div>
""", unsafe_allow_html=True)
