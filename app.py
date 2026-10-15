import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
import re
import zipfile

# 1. 페이지 레이아웃 및 기본 고정 설정
st.set_page_config(page_title="채밍밍의 캐러셀 자동 메이커", layout="wide")
st.title("📸 인스타 캐러셀 자동 메이커")
st.markdown("AI와 대화하며 완성한 대본을 아래 칸에 입력만 하세요! 고품질 인스타 피드 이미지로 자동 전환됩니다.")

FONT_PATH = "malgunbd.ttf"

PREMIUM_COLORS = {
    "딥 블랙 (Deep Black)": "#191919", "오프 화이트 (Off White)": "#F5F5F7",
    "크림 옐로우 (Cream Gold)": "#F4E0A5", "소프트 모브 (Soft Mauve)": "#C3B1E1",
    "무드 버건디 (Burgundy)": "#4A0E17", "올리브 카키 (Olive Khaki)": "#4B5320",
    "브릭 오렌지 (Brick Red)": "#B84A39",
}

ASPECT_RATIOS = {
    "Square (1:1) - 인스타피드/블로그": (1080, 1080),
    "Portrait (3:4) - 인스타 추천 카드뉴스": (1080, 1440),
    "Vertical (9:16) - 릴스/쇼츠/틱톡": (1080, 1920),
    "Widescreen (16:9) - 유튜브 썸네일": (1920, 1080)
}

# --- [상태 초기화 보정 시스템] ---
if "slides" not in st.session_state:
    st.session_state.slides = [
        {"title": "여기에 인스타 **헤드라인**을 적으세요", "content": "여기에 본문 요약 내용을 적으세요.\n**별표 두개**를 앞뒤로 감싸면 강조색이 적용됩니다!"},
        {"title": "", "content": "내용을 채워 넣으시면 실시간 프리뷰에 반영됩니다."}
    ]
if "current_page_idx" not in st.session_state:
    st.session_state.current_page_idx = 0

# 2. 왼쪽 사이드바 커스텀 스타일 제어 UI (규격 및 배치 제거 완료)
st.sidebar.markdown("---")
st.sidebar.subheader("🔤 글자 크기 비율 조절")
title_percent = st.sidebar.slider("📐 제목 글자 크기 비율", 1, 100, 65, format="%d%%")
content_percent = st.sidebar.slider("📐 본문 글자 크기 비율", 1, 100, 35, format="%d%%")

title_size = int((title_percent / 100) * 150) + 15
content_size = int((content_percent / 100) * 90) + 10

st.sidebar.markdown("---")
st.sidebar.subheader("🎨 감성 컬러셋 조합")
text_color = PREMIUM_COLORS[st.sidebar.selectbox("기본 글자 색상", list(PREMIUM_COLORS.keys()), index=1)]
highlight_color = PREMIUM_COLORS[st.sidebar.selectbox("🌟 중요 강조 단어 색상", list(PREMIUM_COLORS.keys()), index=2)]
bg_color = PREMIUM_COLORS[st.sidebar.selectbox("🖼️ 배경 컬러 에디션", list(PREMIUM_COLORS.keys()), index=0)]

# 3. 메인 레이아웃 화면 구성 (좌측: 원고 편집 / 우측: 프리뷰 및 규격 배치)
left_col, right_col = st.columns([1, 1.2])

with left_col:
    st.subheader("📝 카드뉴스 원고 편집 폼")
    st.info("💡제목과 본문을 입력하고, 필요한 경우 배경 사진을 업로드하세요.")
    
    temp_slides = []
    for i, slide in enumerate(st.session_state.slides):
        with st.expander(f"📁 슬라이드 {i+1} 장", expanded=True):
            t = st.text_input(f"제목 {i+1}", value=slide["title"], key=f"title_{i}")
            c = st.text_area(f"본문 {i+1}", value=slide["content"], key=f"content_{i}", height=100)
            
            img_key = f"file_{i}"
            if img_key not in st.session_state:
                st.session_state[img_key] = None
                
            uploaded_file = st.file_uploader(f"📸 슬라이드 {i+1}의 배경 사진 올리기", type=["jpg", "jpeg", "png"], key=f"img_upload_{i}")
            if uploaded_file:
                st.session_state[img_key] = uploaded_file
                
            temp_slides.append({"title": t, "content": c, "file": st.session_state[img_key]})
            
            if st.button(f"🗑️ {i+1}번 슬라이드 삭제", key=f"del_{i}"):
                if len(st.session_state.slides) > 1:
                    st.session_state.slides.pop(i)
                    st.session_state.current_page_idx = min(st.session_state.current_page_idx, len(st.session_state.slides)-1)
                    st.rerun()

    st.session_state.slides = temp_slides
    
    if st.button("➕ 새 슬라이드 추가", type="secondary", use_container_width=True):
        st.session_state.slides.append({"title": "새 슬라이드 **제목**", "content": "새 내용", "file": None})
        st.rerun()

# 4. 이미지 그래픽 처리 함수부
def draw_styled_line(draw, line, start_x, y, font, base_color, high_color):
    tokens = re.split(r'(\*\*.*?\*\*)', line)
    current_x = start_x
    for token in tokens:
        if token.startswith('**') and token.endswith('**'):
            text = token[2:-2]
            color = high_color
        else:
            text = token
            color = base_color
        if not text: continue
        draw.text((current_x, y), text, font=font, fill=color)
        bbox = draw.textbbox((0, 0), text, font=font)
        current_x += (bbox[2] - bbox[0])

def draw_carousel_slide(title, content, font_path, t_size, c_size, t_color, h_color, bg_hex, slide_file, align, t_y, c_y, t_w, t_h):
    if slide_file is not None:
        try:
            img = Image.open(slide_file).convert("RGB").resize((t_w, t_h))
        except:
            img = Image.new("RGB", (t_w, t_h), bg_hex)
    else:
        img = Image.new("RGB", (t_w, t_h), bg_hex)
        
    draw = ImageDraw.Draw(img)
    width, height = img.size
    try:
        font_title = ImageFont.truetype(font_path, t_size)
        font_content = ImageFont.truetype(font_path, c_size)
    except:
        font_title = font_content = ImageFont.load_default()

    wrap_t_width = int(16 * (t_w / 1080))
    wrap_c_width = int(24 * (t_w / 1080))

    t_lines = textwrap.wrap(title, width=max(8, wrap_t_width))
    current_y = t_y
    for line in t_lines:
        clean_line = line.replace("**", "")
        bbox = draw.textbbox((0, 0), clean_line, font=font_title)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        start_x = 80 if align == "왼쪽" else (width - line_width - 80 if align == "오른쪽" else (width - line_width) / 2)
        draw_styled_line(draw, line, start_x, current_y, font_title, t_color, h_color)
        current_y += line_height + 25

    c_lines = []
    for chunk in content.split('\n'):
        if chunk.strip():
            c_lines.extend(textwrap.wrap(chunk, width=max(12, wrap_c_width)))
            
    current_y = c_y
    for line in c_lines:
        clean_line = line.replace("**", "")
        bbox = draw.textbbox((0, 0), clean_line, font=font_content)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        start_x = 80 if align == "왼쪽" else (width - line_width - 80 if align == "오른쪽" else (width - line_width) / 2)
        draw_styled_line(draw, line, start_x, current_y, font_content, t_color, h_color)
        current_y += line_height + 20
    return img

# 5. 오른쪽 화면 구성 (5:5 분할 및 프리뷰 사이즈 30% 고정)
with right_col:
    st.subheader("👁️ 실시간 프리뷰 & 규격 배치 셋업")
    
    # 우측 공간을 프리뷰와 설정창으로 정확히 5:5(1:1 비율) 분할
    preview_col, config_col = st.columns([1, 1])
    
    with config_col:
        st.markdown("### 📐 규격 및 글자 배치")
        selected_ratio_name = st.selectbox("원하는 이미지 규격을 고르세요", list(ASPECT_RATIOS.keys()))
        target_width, target_height = ASPECT_RATIOS[selected_ratio_name]

        align_option = st.radio("글자 가로 정렬", ["왼쪽", "중앙", "오른쪽"], index=1, horizontal=True)
        title_y_pos = st.slider("제목 세로 위치", 50, 800, 200, 10)
        content_y_pos = st.slider("본문 세로 위치", 200, 1600, 650, 10)
        
    with preview_col:
        # 프리뷰 연산 수행
        all_images = [draw_carousel_slide(s["title"], s["content"], FONT_PATH, title_size, content_size, text_color, highlight_color, bg_color, s["file"], align_option, title_y_pos, content_y_pos, target_width, target_height) for s in st.session_state.slides]
        
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        total_pages = len(all_images)
        current_idx = st.session_state.current_page_idx
        
        with nav_col1:
            if st.button("⬅️ 이전 장", use_container_width=True) and current_idx > 0:
                st.session_state.current_page_idx -= 1
                st.rerun()
        with nav_col2:
            st.markdown(f"<h4 style='text-align: center; color: gray;'> {current_idx + 1} / {total_pages}</h4>", unsafe_allow_html=True)
        with nav_col3:
            if st.button("다음 장 ➡️", use_container_width=True) and current_idx < total_pages - 1:
                st.session_state.current_page_idx += 1
                st.rerun()

        if all_images and current_idx < len(all_images):
            current_img = all_images[current_idx]
            # 프리뷰 슬라이더 바를 없애고 30% 크기로 완전 고정
            preview_scale = 30
            resized_preview = current_img.resize((int(current_img.width * (preview_scale/100)), int(current_img.height * (preview_scale/100))))
            st.image(resized_preview, caption=f"실시간 프리뷰 (30% 고정 완료)", use_container_width=False)
            
    st.markdown("---")
    st.subheader("💾 다운로드")
    if st.button("🎁 게시물 업로드용 이미지 한 번에 다운로드 (ZIP)", use_container_width=True, type="primary") and all_images:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, img in enumerate(all_images):
                img_buffer = BytesIO()
                img.save(img_buffer, format="JPEG")
                zip_file.writestr(f"{idx + 1}.jpg", img_buffer.getvalue())
        
        st.download_button(
            label="📥 ZIP 압축파일 다운로드 받기",
            data=zip_buffer.getvalue(),
            file_name="premium_carousel.zip",
            mime="application/zip",
            use_container_width=True
        )
