import streamlit as st
import requests
import io
from PIL import Image
from huggingface_hub import InferenceClient

# 1. 페이지 설정
st.set_page_config(page_title="AI 창작자 작업실", layout="wide")

# 2. 세션 상태 초기화 (★반드시 다른 모든 코드보다 상단에 위치해야 함★)
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "hf_token" not in st.session_state:
    st.session_state["hf_token"] = ""
if "img_history" not in st.session_state:
    st.session_state["img_history"] = []
if "novel_draft" not in st.session_state:
    st.session_state["novel_draft"] = ""
if "playlists_dict" not in st.session_state:
    # 기본 재생목록 생성
    st.session_state["playlists_dict"] = {"기본 재생목록": []}
if "current_playlist_name" not in st.session_state:
    st.session_state["current_playlist_name"] = "기본 재생목록"
if "current_track_index" not in st.session_state:
    st.session_state["current_track_index"] = 0
if "theme" not in st.session_state:
    st.session_state["theme"] = "Default"

# --- [3번: 테마별 스타일 정의] ---
def apply_theme(theme_name):
    """
    매개변수 theme_name을 받아 선택된 테마의 CSS를 적용합니다.
    """
    if theme_name == "Retro Arcade":
        st.markdown("""
            <style>
            /* 1. 배경 설정 */
            .stApp {
                background-color: #1e130c !important;
                background-image: linear-gradient(rgba(30, 19, 12, 0.95), rgba(30, 19, 12, 0.95)), 
                                  url('https://www.transparenttextures.com/patterns/dark-wood.png') !important;
            }

            /* 2. 제목 및 강조 텍스트 */
            h1, h2, h3, .stSubheader {
                color: #fceabb !important;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.8) !important;
            }

            /* 3. [추가] 일반 텍스트 및 사이드바 라벨 가독성 보강 */
            /* '이동할 구역을 선택하세요' 등 모든 라벨과 일반 글자 */
            p, span, label, .stMarkdown, [data-testid="stWidgetLabel"] p {
                color: #d4af37 !important; /* 금색으로 변경 */
                font-weight: 500 !important;
            }

            /* 4. 버튼 디자인: 스크린샷 17 스타일 유지 */
            div.stButton > button, div.stLinkButton > a {
                background-color: #000000 !important;
                color: #d4af37 !important;
                border: 2px solid #d4af37 !important;
                border-radius: 10px !important;
                font-weight: bold !important;
                height: 55px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                text-decoration: none !important;
            }
            div.stButton > button:hover, div.stLinkButton > a:hover {
                background-color: #1a1a1a !important;
                color: #fceabb !important;
                border-color: #fceabb !important;
            }

            /* 5. 수첩(Expander) 및 시스템 문구 제거 */
            [data-testid="stExpanderToggleIcon"] + div, 
            details summary svg + div,
            details summary span[class*="StyledInstruction"] {
                display: none !important;
            }
            details summary p {
                color: #ffffff !important; /* 수첩 제목은 흰색 유지하여 눈에 띄게 함 */
                font-weight: bold !important;
            }
            div[data-testid="stExpander"] {
                border: 1px solid rgba(212, 175, 55, 0.3) !important;
                background-color: rgba(0, 0, 0, 0.4) !important;
            }

            /* 6. 입력창 가독성 유지 */
            .stTextInput input, .stTextArea textarea {
                background-color: #121212 !important;
                color: #ffffff !important;
                line-height: 2.0 !important;
                padding: 15px !important;
                border: 1px solid #d4af37 !important;
            }

            /* 7. 사이드바 배경 및 테두리 */
            section[data-testid="stSidebar"] {
                background-color: #0c0c0c !important;
                border-right: 2px solid #d4af37 !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
    elif theme_name == "Cyber Future":
        st.markdown("""
            <style>
            /* 전체 배경: 깊은 밤하늘 그라데이션 */
            .stApp {
                background: linear-gradient(180deg, #050b1a 0%, #0a1931 50%, #1a3c5a 100%) !important;
                background-attachment: fixed !important;
            }

            /* [수정] 버튼 및 링크 상자: 은하수 블루 스타일 */
            /* Daily Free Credits Sites 밑의 상자들에 적용됨 */
            div.stButton > button, div.stLinkButton > a {
                background: rgba(0, 150, 255, 0.15) !important; /* 반투명 블루 */
                color: #ffffff !important;
                border: 1px solid rgba(0, 242, 255, 0.5) !important; /* 네온 블루 테두리 */
                border-radius: 12px !important;
                height: 55px !important;
                backdrop-filter: blur(10px) !important;
                font-weight: bold !important;
                text-shadow: 0 0 8px rgba(0, 242, 255, 0.8) !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                text-decoration: none !important;
            }
            div.stButton > button:hover, div.stLinkButton > a:hover {
                background: rgba(0, 242, 255, 0.3) !important;
                border-color: #ffffff !important;
                box-shadow: 0 0 20px rgba(0, 242, 255, 0.4) !important;
            }

            /* [수정] 수첩(Expander) 및 기타 상자 */
            div[data-testid="stExpander"] {
                background-color: rgba(255, 255, 255, 0.05) !important;
                backdrop-filter: blur(15px) !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 15px !important;
            }
            details summary p {
                color: #e0f2ff !important;
                font-size: 1.1rem !important;
            }

            /* 사이드바 스타일링 */
            section[data-testid="stSidebar"] {
                background-color: rgba(5, 11, 26, 0.85) !important;
                backdrop-filter: blur(20px);
                border-right: 1px solid rgba(0, 242, 255, 0.2) !important;
            }
            
            /* 글자색 통일 */
            p, span, label, [data-testid="stWidgetLabel"] p {
                color: #b0d4ff !important;
            }
            h1, h2, h3 {
                color: #ffffff !important;
                text-shadow: 0 0 15px rgba(0, 150, 255, 0.6) !important;
            }
            </style>
        """, unsafe_allow_html=True)

# --- [함수 호출부 확인] ---
# 테마 적용 실행 시 아래처럼 세션 상태의 값을 전달해야 합니다.
apply_theme(st.session_state["theme"])
# 3. 모델 클라이언트 최적화 (캐싱)
@st.cache_resource
def get_hf_client(token):
    return InferenceClient(model="black-forest-labs/FLUX.1-schnell", token=token)

# 4. 토큰 유효성 검사 함수
def verify_token(token):
    api_url = "https://huggingface.co/api/whoami-v2"
    headers = {"Authorization": f"Bearer {token.strip()}"}
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return True, response.json().get("name", "User")
        else:
            return False, "토큰이 유효하지 않습니다."
    except Exception as e:
        return False, f"연결 오류: {str(e)}"

# --- [로그인 화면 시작] ---
# 이제 여기서 authenticated를 불러와도 에러가 나지 않습니다.
if not st.session_state["authenticated"]:
    st.title("🔐 작업실 입장 (HF 인증)")
    st.write("서비스 이용을 위해 Hugging Face 'Read' 토큰이 필요합니다.")
    
    # 토큰 입력창 (비밀번호 형식)
    input_token = st.text_input("Hugging Face Access Token (hf_...)", type="password")
    
    if st.button("토큰 인증 및 입장"):
        if input_token.startswith("hf_"):
            with st.spinner("토큰 유효성을 확인 중입니다..."):
                is_valid, user_name = verify_token(input_token)
                
                if is_valid:
                    st.success(f"✅ 인증 성공! 환영합니다, {user_name}님.")
                    st.session_state["authenticated"] = True
                    st.session_state["hf_token"] = input_token
                    st.rerun()
                else:
                    st.error(f"❌ 인증 실패: {user_name}")
        else:
            st.warning("토큰은 'hf_'로 시작해야 합니다.")
    
    st.stop() # 인증 전까지는 아래 내용을 보여주지 않음

# --- [인증 후 메인 화면] ---

# --- [최상단 초기화 섹션] ---
if "img_history" not in st.session_state:
    st.session_state["img_history"] = []

if "novel_draft" not in st.session_state:
    st.session_state["novel_draft"] = ""

# (기존의 authenticated 초기화 코드 등...)
# --- [인증 후 메인 화면 하단에 추가] ---

# --- [탭 1] AI 이미지 생성소 (기존 내용을 아래 하위 탭 구조로 교체) ---
# --- [인증 후 메인 화면] ---

# 1. 사이드바 메뉴 설정 (에러 방지를 위해 위로 올림)
with st.sidebar:
    st.title("🌌 COSMOS MENU")
    menu = st.radio(
        "이동할 구역을 선택하세요",
        ["🎨 이미지 생성소", "✍️ 스토리 빌더", "📌 창작 리소스", "🎵 작업실 환경"],
        index=0
    )
    st.divider()
    
    # 테마 설정 UI
    st.title("🎨 테마 설정")
    selected_theme = st.selectbox(
        "작업실 스킨 선택", 
        ["Default", "Retro Arcade", "Cyber Future"], 
        index=["Default", "Retro Arcade", "Cyber Future"].index(st.session_state["theme"])
    )
    if selected_theme != st.session_state["theme"]:
        st.session_state["theme"] = selected_theme
        st.rerun()
    st.divider()

    # 이미지 보관함 (사이드바 하단)
    st.title("📂 이미지 보관함")
    if st.session_state["img_history"]:
        if st.button("🗑️ 히스토리 삭제"):
            st.session_state["img_history"] = []
            st.rerun()
        for idx, item in enumerate(st.session_state["img_history"]):
            with st.expander(f"기록 {idx + 1}"):
                st.image(item["image"], use_container_width=True)
    else:
        st.info("기록이 없습니다.")

# 2. 메인 콘텐츠 영역 (선택된 메뉴에 따라 출력)
if menu == "🎨 이미지 생성소":
    st.header("🎨 Image Generation Hub")
    sub_tab_external, sub_tab_hf, sub_tab_comfy = st.tabs([
        "🌐 외부 무료 사이트", "☁️ Hugging Face (Cloud)", "💻 ComfyUI (Local)"
    ])
    
    with sub_tab_external:
        st.subheader("🔗 Daily Free Credits Sites")
        col1, col2, col3 = st.columns(3)
        with col1: st.link_button("Civitai 바로가기", "https://civitai.com/generate", use_container_width=True)
        with col2: st.link_button("SeaArt 바로가기", "https://www.seaart.ai/", use_container_width=True)
        with col3: st.link_button("Tensor.art 바로가기", "https://tensor.art/", use_container_width=True)
        
        with st.expander("📝 나의 계정 수첩"):
            st.text_area("계정 정보 입력", placeholder="예: Civitai - id / pw")

    with sub_tab_hf:
        hf_prompt = st.text_input("그림 묘사 (영문)", key="hf_p")
        if st.button("Hugging Face 생성 실행"):
            client = get_hf_client(st.session_state["hf_token"])
            with st.spinner("그리는 중..."):
                image = client.text_to_image(hf_prompt)
                st.session_state["img_history"].insert(0, {"image": image, "prompt": hf_prompt})
                st.image(image, use_container_width=True)

elif menu == "✍️ 스토리 빌더":
    st.header("✍️ AI 시나리오 빌더")
    col_write, col_ai = st.columns([2, 1])
    with col_write:
        st.session_state["novel_draft"] = st.text_area("스토리 메모장", value=st.session_state["novel_draft"], height=450)
        st.download_button("📄 파일로 저장", st.session_state["novel_draft"], file_name="story.txt")
    with col_ai:
        st.subheader("🤖 AI 파트너")
        st.link_button("✨ Gemini", "https://gemini.google.com/app", use_container_width=True)
        st.link_button("💬 ChatGPT", "https://chatgpt.com", use_container_width=True)

elif menu == "📌 창작 리소스":
    st.header("📌 Creative Resources Hub")
    st.write("각 카테고리를 클릭하면 유용한 사이트 목록이 나타납니다.")

    # 1. 레퍼런스 & 커뮤니티 (서랍)
    with st.expander("🎨 레퍼런스 & 아트 커뮤니티", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.link_button("Pinterest", "https://www.pinterest.com/", use_container_width=True)
            st.link_button("Pixiv", "https://www.pixiv.net/", use_container_width=True)
        with col2:
            st.link_button("ArtStation", "https://www.artstation.com/", use_container_width=True)
            st.link_button("Civitai", "https://civitai.com/", use_container_width=True)

    # 2. 고화질 이미지 & 에셋 (서랍)
    with st.expander("📸 고화질 사진 & 에셋"):
        col1, col2 = st.columns(2)
        with col1:
            st.link_button("Unsplash", "https://unsplash.com/", use_container_width=True)
            st.link_button("Pexels", "https://www.pexels.com/ko-kr/", use_container_width=True)
        with col2:
            st.link_button("Pixabay", "https://pixabay.com/", use_container_width=True)
            st.link_button("Flaticon (아이콘)", "https://www.flaticon.com/", use_container_width=True)

    # 3. 인체 구조 & 포즈 (서랍)
    with st.expander("🧍 인체 & 포즈 레퍼런스"):
        col1, col2 = st.columns(2)
        with col1:
            st.link_button("Posemaniacs", "https://www.posemaniacs.com/", use_container_width=True)
            st.link_button("Line of Action (크로키)", "https://line-of-action.com/", use_container_width=True)
        with col2:
            st.link_button("MagicPoser (3D)", "https://magicposer.com/", use_container_width=True)
            st.link_button("Adorkastock", "https://www.adorkastock.com/sketch/", use_container_width=True)

    # 4. 컬러 & 디자인 도구 (서랍)
    with st.expander("🌈 컬러 & 디자인 유틸리티"):
        col1, col2 = st.columns(2)
        with col1:
            st.link_button("Adobe Color", "https://color.adobe.com/", use_container_width=True)
            st.link_button("Coolors", "https://coolors.co/", use_container_width=True)
        with col2:
            st.link_button("눈누 (무료 폰트)", "https://noonnu.cc/", use_container_width=True)
            st.link_button("Canva", "https://www.canva.com/", use_container_width=True)

    # 5. ✨ 다모아 AI pick: 유용한 AI 창작 도구 (서랍)
    with st.expander("✨ AI 창작 보조 도구 (다모아 pick)"):
        st.write("다모아 AI에서 엄선한 그림 및 글쓰기 유틸리티입니다.")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**[이미지 편집/보정]**")
            st.link_button("Upscale.media (화질 개선)", "https://www.upscale.media/ko", use_container_width=True)
            st.link_button("Cleanup.pictures (개체 제거)", "https://cleanup.pictures/", use_container_width=True)
            st.link_button("Remove.bg (배경 제거)", "https://www.remove.bg/ko", use_container_width=True)
        with col2:
            st.markdown("**[글쓰기/아이디어]**")
            st.link_button("뤼튼 (Wrtn - 한국어 특화)", "https://wrtn.ai/", use_container_width=True)
            st.link_button("Copy.ai (카피라이팅 보조)", "https://www.copy.ai/", use_container_width=True)
            st.link_button("DeepL (자연스러운 번역)", "https://www.deepl.com/translator", use_container_width=True)

    st.divider()
    st.info("💡 각 항목을 클릭하여 서랍을 열고 닫을 수 있습니다.")

elif menu == "🎵 작업실 환경":
    st.header("🎵 스마트 작업실 오디오 매니저")

    # --- [재생목록 관리 상단바] ---
    with st.expander("📂 재생목록 관리 (목록 생성/변경)", expanded=False):
        col_list, col_add = st.columns([2, 1])
        with col_list:
            plist_names = list(st.session_state["playlists_dict"].keys())
            selected_plist = st.selectbox("불러올 재생목록", plist_names, 
                                          index=plist_names.index(st.session_state["current_playlist_name"]))
            if selected_plist != st.session_state["current_playlist_name"]:
                st.session_state["current_playlist_name"] = selected_plist
                st.session_state["current_track_index"] = 0 # 목록 변경 시 첫 곡으로
                st.rerun()
        
        with col_add:
            new_plist_name = st.text_input("새 목록 이름", placeholder="예: 코딩 집중")
            if st.button("✨ 새 목록 만들기", use_container_width=True):
                if new_plist_name and new_plist_name not in st.session_state["playlists_dict"]:
                    st.session_state["playlists_dict"][new_plist_name] = []
                    st.session_state["current_playlist_name"] = new_plist_name
                    st.success(f"'{new_plist_name}' 목록이 생성되었습니다.")
                    st.rerun()

    st.divider()

    # 현재 활성화된 재생목록 참조
    curr_name = st.session_state["current_playlist_name"]
    active_list = st.session_state["playlists_dict"][curr_name]

    # --- [메인 레이아웃] ---
    p_col1, p_col2 = st.columns([1, 1])

    with p_col1:
        st.subheader(f"📻 Now Playing: {curr_name}")
        if active_list:
            idx = st.session_state["current_track_index"]
            # 인덱스 범위 초과 방지
            if idx >= len(active_list): idx = 0
            
            track = active_list[idx]
            if track['type'] == 'youtube':
                st.video(track['url'])
            else:
                st.audio(track['url'])
            st.info(f"재생 중: {track['title']}")
        else:
            st.warning("이 재생목록은 비어 있습니다. 곡을 추가해 주세요.")
            st.video("https://www.youtube.com/watch?v=jfKfPfyJRdk")

    with p_col2:
        st.subheader("➕ 현재 목록에 곡 추가")
        add_mode = st.radio("추가 방식", ["YouTube 링크", "내 컴퓨터 파일"], horizontal=True)
        
        if add_mode == "YouTube 링크":
            yt_url = st.text_input("YouTube URL")
            yt_title = st.text_input("곡 제목 (YouTube)")
            if st.button("추가하기 (YT)", use_container_width=True):
                if yt_url and yt_title:
                    st.session_state["playlists_dict"][curr_name].append({"type": "youtube", "url": yt_url, "title": yt_title})
                    st.rerun()
        else:
            local_file = st.file_uploader("음악 파일 업로드", type=["mp3", "wav"])
            if local_file and st.button("추가하기 (Local)", use_container_width=True):
                st.session_state["playlists_dict"][curr_name].append({
                    "type": "local", "url": local_file, "title": f"📂 {local_file.name}"
                })
                st.rerun()

    # --- [하단 재생목록 리스트 및 컨트롤] ---
    st.write(f"### 📜 {curr_name} 리스트")
    if active_list:
        for i, item in enumerate(active_list):
            c_play, c_del = st.columns([5, 1])
            with c_play:
                btn_label = f"▶️ {item['title']}" if i == st.session_state["current_track_index"] else item['title']
                if st.button(btn_label, key=f"play_{curr_name}_{i}", use_container_width=True):
                    st.session_state["current_track_index"] = i
                    st.rerun()
            with c_del:
                if st.button("❌", key=f"del_{curr_name}_{i}"):
                    st.session_state["playlists_dict"][curr_name].pop(i)
                    st.rerun()

        # 제어 바
        st.write("---")
        ctrl_1, ctrl_2, ctrl_3 = st.columns(3)
        with ctrl_1:
            if st.button("⏮️ 이전 곡", use_container_width=True):
                st.session_state["current_track_index"] = (st.session_state["current_track_index"] - 1) % len(active_list)
                st.rerun()
        with ctrl_2:
            st.markdown(f"<center><b>{st.session_state['current_track_index']+1} / {len(active_list)}</b></center>", unsafe_allow_html=True)
        with ctrl_3:
            if st.button("⏭️ 다음 곡", use_container_width=True):
                st.session_state["current_track_index"] = (st.session_state["current_track_index"] + 1) % len(active_list)
                st.rerun()