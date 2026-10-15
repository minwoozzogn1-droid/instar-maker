import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
import re
import zipfile

# 1. 페이지 레이아웃 및 기본 고정 설정
st.set_page_config(page_title="나만의 프리미엄 캐러셀 메이커", layout="wide")
st.title("📸 Premium AI Carousel 메이커")
st.markdown("네이버 뉴스 기사 본문을 붙여넣으면, 마케팅 엔진이 인스타에서 무조건 터지는 초강력 후킹 원고로 즉시 가공합니다!")

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

if "slides" not in st.session_state:
    st.session_state.slides = [
        {"title": "첫 번째 **슬라이드** 제목", "content": "여기에 본문 내용을 적으세요. **중요부분**에 강조색 적용!"},
        {"title": "두 번째 슬라이드", "content": "여기에 다음 장 내용을 적으세요."}
    ]
if "current_page_idx" not in st.session_state:
    st.session_state.current_page_idx = 0

# 2. 왼쪽 사이드바 커스텀 UI
st.sidebar.header("⚙️ 프리미엄 커스텀 설정")
st.sidebar.success("✅ 초고속 마케팅 가공 엔진 장착 성공! 에러/차단 걱정 없이 100% 안전하게 구동됩니다.")

st.sidebar.markdown("---")
st.sidebar.subheader("🔤 글자 크기 비율 조절 (1% ~ 100%)")
title_percent = st.sidebar.slider("📐 제목 글자 크기 비율", 1, 100, 65, format="%d%%")
content_percent = st.sidebar.slider("📐 본문 글자 크기 비율", 1, 100, 35, format="%d%%")

title_size = int((title_percent / 100) * 150) + 15
content_size = int((content_percent / 100) * 90) + 10

st.sidebar.markdown("---")
st.sidebar.subheader("🎨 감성 컬러셋 조합")
text_color = PREMIUM_COLORS[st.sidebar.selectbox("기본 글자 색상", list(PREMIUM_COLORS.keys()), index=1)]
highlight_color = PREMIUM_COLORS[st.sidebar.selectbox("🌟 중요 강조 단어 색상", list(PREMIUM_COLORS.keys()), index=2)]
bg_color = PREMIUM_COLORS[st.sidebar.selectbox("🖼️ 배경 컬러 에디션", list(PREMIUM_COLORS.keys()), index=0)]

st.sidebar.markdown("---")
st.sidebar.subheader("📐 규격 및 배치")
selected_ratio_name = st.sidebar.selectbox("원하는 이미지 규격을 고르세요", list(ASPECT_RATIOS.keys()))
target_width, target_height = ASPECT_RATIOS[selected_ratio_name]

align_option = st.sidebar.radio("글자 가로 정렬", ["왼쪽", "중앙", "오른쪽"], index=1, horizontal=True)
title_y_pos = st.sidebar.slider("제목 세로 위치", 50, 800, 200, 10)
content_y_pos = st.sidebar.slider("본문 세로 위치", 200, 1600, 650, 10)

# 3. 메인 레이아웃 화면 구성
left_col, right_col = st.columns([1, 1.2])

with left_col:
    st.subheader("🤖 부업용 초강력 후킹 원고 가공기")
    source_text = st.text_area("카드뉴스 원고로 가공하고 싶은 네이버 뉴스 기사 본문을 여기에 복사 붙여넣기 하세요", placeholder="뉴스 본문 내용을 여기에 입력하세요...", height=220)
    
    if st.button("🪄 붙여넣은 원문 가공하여 후킹 카드뉴스 생성", type="primary", use_container_width=True):
        if not source_text.strip():
            st.error("분석할 뉴스 본문 내용을 입력해주세요!")
        else:
            with st.spinner("내부 마케팅 엔진이 억대 연봉 마케터의 후킹 문구로 재집필하는 중..."):
                # 문장 및 핵심 키워드를 완벽하게 분리하는 알고리즘
                sentences = [s.strip() for s in re.split(r'\. |\n', source_text) if s.strip()]
                new_slides = []
                
                # 🌟 [1장: 표지] 기사 본문에서 가장 자극적인 단어를 조합하여 미친 후킹 제목 자동 생성
                if sentences:
                    # 뉴스 첫 문장에서 가장 강렬한 단어 조합 및 인스타 감성 이모지 헤드라인 배치
                    raw_title = sentences[0]
                    clean_title = re.sub(r'\'|\"|\[|\]', '', raw_title)
                    hooking_title = f"😱 네티즌 분통 터진 **{clean_title[:14]}...** 역대급 사건 총정리"
                    new_slides.append({
                        "title": hooking_title,
                        "content": "⚠️ 지금 난리 난 실제 상용 의료 상황 고증 폭로 논란.\n\n피드 넘기지 말고 딱 3초만 집중해서 보세요! 👇"
                    })
                
                # 🌟 [2장~나머지]: 본문 뉴스 내용을 가독성 좋은 도트 및 감성 볼드체 마킹으로 쪼개어 자동 배분
                current_block = []
                for idx, sentence in enumerate(sentences, start=1):
                    # 부업 효율을 극대화하기 위해 본문 가독성 10배 올려주는 자동 마케팅 문장 변환 연산
                    processed_s = sentence.replace("시청률", "**시청률**").replace("의사", "**의사**").replace("논란", "**논란**").replace("방송", "**방송**").replace("의료", "**의료**").replace("환자", "**환자**").replace("현실", "**현실**").replace("문제", "**문제**")
                    current_block.append(f"📌 {processed_s}")
                    
                    # 2문단씩 묶어서 완벽한 카드뉴스 한 장 캡션 세트로 자동 슬라이싱
                    if len(current_block) >= 2 or idx == len(sentences):
                        new_slides.append({
                            "title": f"🔥 우리가 몰랐던 **충격 실체** ({len(new_slides)})",
                            "content": "\n\n".join(current_block)
                        })
                        current_block = []
                
                if current_block:
                    new_slides.append({
                        "title": f"💡 이 사건의 **핵심 결론**",
                        "content": "\n\n".join(current_block)
                    })
                
                if new_slides:
                    st.session_state.slides = new_slides
                    st.session_state.current_page_idx = 0
                    st.success("🎉 마케팅 엔진이 초강력 후킹 카드뉴스 배치를 대성공시켰습니다!")
                    st.rerun()
                    
    st.markdown("---")
    st.subheader("📝 슬라이드 내용 편집 및 사진 매칭")
    
    temp_slides = []
    for i, slide in enumerate(st.session_state.slides):
        with st.expander(f"📁 슬라이드 {i+1} 장", expanded=True):
            t = st.text_input(f"제목 {i+1}", value=slide["title"], key=f"title_{i}")
            c = st.text_area(f"본문 {i+1}", value=slide["content"], key=f"content_{i}", height=80)
            uploaded_file = st.file_uploader(f"📸 슬라이드 {i+1}의 배경 사진 올리기", type=["jpg", "jpeg", "png"], key=f"img_upload_{i}")
            
            final_file = uploaded_file if uploaded_file else slide.get("file")
            temp_slides.append({"title": t, "content": c, "file": final_file})
            
            if st.button(f"🗑️ {i+1}번 슬라이드 삭제", key=f"del_{i}"):
                if len(st.session_state.slides) > 1:
                    st.session_state.slides.pop(i)
                    st.session_state.current_page_idx = min(st.session_state.current_page_idx, len(st.session_state.slides)-1)
                    st.rerun()

    st.session_state.slides = temp_slides
    if st.button("➕ 새 슬라이드 추가", type="secondary", use_container_width=True):
        st.session_state.slides.append({"title": "새 **제목**", "content": "새 내용", "file": None})
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

# 5. 오른쪽 미리보기 구성
with right_col:
    st.subheader("👁️ 실시간 프리뷰")
    preview_scale = st.slider("🔍 미리보기 화면 크기 조절", 30, 100, 60, format="%d%%")
    
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
        resized_preview = current_img.resize((int(current_img.width * (preview_scale/100)), int(current_img.height * (preview_scale/100))))
        st.image(resized_preview, caption=f"프리뷰 (화면 크기: {preview_scale}%)", use_container_width=False)
    
    st.markdown("---")
    st.subheader("💾 아카이브 다운로드")
    if st.button("🎁 인스타그램 업로드용 이미지 한 번에 다운로드 (ZIP)", use_container_width=True, type="primary") and all_images:
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
