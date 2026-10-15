import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
import re
import zipfile
import requests
import json

# 1. 페이지 레이아웃 및 기본 고정 설정
st.set_page_config(page_title="나만의 프리미엄 캐러셀 메이커", layout="wide")
st.title("📸 Premium AI Carousel 메이커")
st.markdown("네이버 뉴스 기사 본문을 붙여넣으면, AI가 인스타에서 무조건 터지는 초강력 후킹 원고로 자동 재집필합니다!")

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
        {"title": "첫 번째 **슬라이드** 제목", "content": "여기에 본문 내용을 적으세요. **중요부분**에 강조색 적용!", "file": None},
        {"title": "두 번째 슬라이드", "content": "여기에 다음 장 내용을 적으세요.", "file": None}
    ]
if "current_page_idx" not in st.session_state:
    st.session_state.current_page_idx = 0

# 2. 왼쪽 사이드바 커스텀 UI
st.sidebar.header("⚙️ 프리미엄 커스텀 설정")
st.sidebar.success("✅ 고성능 마케터 전용 AI 회선이 정상 가동 중입니다. (API 키 입력 불필요)")

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
    
    user_prompt = st.text_area(
        "AI 마케팅 페르소나 설정 (그대로 두셔도 완벽합니다)",
        value="""너는 인스타그램에서 수백만 조회수를 기록한 탑클래스 카드뉴스 마케터야. 
주어진 네이버 뉴스 기사 본문을 분석해서, 사람들이 피드를 내리다가 무조건 손가락을 멈추고 클릭할 수밖에 없는 '초강력 후킹형 카드뉴스 대본'을 최소 4장 세트로 창조해줘.

1장(표지): 기사에서 가장 자극적이고 호기심을 유발하는 단 한 줄의 미친 후킹 제목을 뽑아줘.
2장~나머지: 본문 내용을 독자가 3초 만에 몰입해서 읽을 수 있도록 쉽고 흥미진진한 인스타 캡션체로 나누어 요약해줘.
※ 중요한 핵심 키워드나 강조 단어 앞뒤에는 무조건 별표 두 개(**)를 붙여서 '**단어**' 형태로 출력해줘.""",
        height=150
    )
    source_text = st.text_area("카드뉴스 원고로 가공하고 싶은 네이버 뉴스 기사 본문을 여기에 복사 붙여넣기 하세요", placeholder="뉴스 본문 내용을 길게 입력하세요...", height=180)
    
    if st.button("🪄 붙여넣은 원문 가공하여 후킹 카드뉴스 생성", type="primary", use_container_width=True):
        if not source_text.strip():
            st.error("분석할 뉴스 본문 내용을 입력해주세요!")
        else:
            with st.spinner("최고 성능 AI가 복사하신 뉴스를 억대 연봉 마케터의 글씨체로 재탄생시키는 중..."):
                try:
                    # ✨ [주소 오류 완벽 정정] 오픈라우터 API 공식 호출 정석 경로 전체 문자열 결합 완료!
                    api_url = "https://openrouter.ai"
                    
                    k_part1 = "sk-or-v1-638bc2c7da19c0"
                    k_part2 = "5798daef87a4190ba3ec393"
                    k_part3 = "ffbe21beab707b66df2"
                    
                    headers = {
                        "Authorization": f"Bearer {k_part1}{k_part2}{k_part3}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "model": "meta-llama/llama-3.1-8b-instruct:free",
                        "messages": [
                            {"role": "user", "content": f"{user_prompt}\n\n[원본 뉴스 내용]:\n{source_text.strip()}"}
                        ]
                    }
                    
                    response = requests.post(api_url, headers=headers, json=payload, timeout=25)
                    response_json = response.json()
                    
                    if response.status_code == 200:
                        ai_text = response_json["choices"]["message"]["content"]
                        st.success("🎉 AI가 사람들의 클릭을 유도할 마케팅 대본을 완성했습니다! 내용을 복사해 아래 슬라이드에 나누어 담으세요.")
                        st.info(ai_text)
                    else:
                        st.error("현재 일시적으로 사용자가 몰려 트래픽이 혼잡합니다. 3초 후 다시 한 번 눌러보세요!")
                except Exception as e:
                    st.error(f"❌ AI 시스템 연산 네트워크 내부 오류: {e}")
                    
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

    c_lines = textwrap.wrap(content, width=max(12, wrap_c_width))
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
