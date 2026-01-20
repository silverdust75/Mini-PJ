import streamlit as st
import requests
import io
from PIL import Image
from huggingface_hub import InferenceClient
from typing import List, Dict, Any, Optional, Tuple

# --- [1. 클래스 기반 모듈화: 유틸리티 및 API 관리] ---

class StyleManager:
    """테마 및 CSS 스타일 적용 클래스"""
    @staticmethod
    def apply_theme(theme_name: str) -> None:
        if theme_name == "Retro Arcade":
            st.markdown("""
                <style>
                .stApp { background-color: #1e130c !important; background-image: linear-gradient(rgba(30, 19, 12, 0.95), rgba(30, 19, 12, 0.95)), url('https://www.transparenttextures.com/patterns/dark-wood.png') !important; }
                h1, h2, h3, .stSubheader { color: #fceabb !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8) !important; }
                p, span, label, .stMarkdown, [data-testid="stWidgetLabel"] p { color: #d4af37 !important; font-weight: 500 !important; }
                div.stButton > button, div.stLinkButton > a { background-color: #000000 !important; color: #d4af37 !important; border: 2px solid #d4af37 !important; border-radius: 10px !important; height: 55px !important; display: flex !important; align-items: center !important; justify-content: center !important; text-decoration: none !important; }
                div.stButton > button:hover, div.stLinkButton > a:hover { background-color: #1a1a1a !important; color: #fceabb !important; border-color: #fceabb !important; }
                details summary p { color: #ffffff !important; font-weight: bold !important; }
                div[data-testid="stExpander"] { border: 1px solid rgba(212, 175, 55, 0.3) !important; background-color: rgba(0, 0, 0, 0.4) !important; }
                .stTextInput input, .stTextArea textarea { background-color: #121212 !important; color: #ffffff !important; border: 1px solid #d4af37 !important; }
                section[data-testid="stSidebar"] { background-color: #0c0c0c !important; border-right: 2px solid #d4af37 !important; }
                </style>
            """, unsafe_allow_html=True)
        elif theme_name == "Cyber Future":
            st.markdown("""
                <style>
                .stApp { background: linear-gradient(180deg, #050b1a 0%, #0a1931 50%, #1a3c5a 100%) !important; background-attachment: fixed !important; }
                div.stButton > button, div.stLinkButton > a { background: rgba(0, 150, 255, 0.15) !important; color: #ffffff !important; border: 1px solid rgba(0, 242, 255, 0.5) !important; border-radius: 12px !important; height: 55px !important; backdrop-filter: blur(10px) !important; font-weight: bold !important; text-shadow: 0 0 8px rgba(0, 242, 255, 0.8) !important; }
                div[data-testid="stExpander"] { background-color: rgba(255, 255, 255, 0.05) !important; backdrop-filter: blur(15px) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; }
                section[data-testid="stSidebar"] { background-color: rgba(5, 11, 26, 0.85) !important; border-right: 1px solid rgba(0, 242, 255, 0.2) !important; }
                p, span, label, [data-testid="stWidgetLabel"] p { color: #b0d4ff !important; }
                h1, h2, h3 { color: #ffffff !important; text-shadow: 0 0 15px rgba(0, 150, 255, 0.6) !important; }
                </style>
            """, unsafe_allow_html=True)

class HFImageGenerator:
    """Hugging Face API 연동 및 에러 처리 클래스"""
    def __init__(self, token: str):
        self.token = token
        self.client = InferenceClient(model="black-forest-labs/FLUX.1-schnell", token=token)

    def generate(self, prompt: str) -> Optional[Any]:
        """이미지 생성 및 상세 에러 처리 로직"""
        try:
            image = self.client.text_to_image(prompt)
            return image
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 429:
                st.error("🚨 [사용량 초과] 무료 토큰 한도에 도달했습니다. 잠시 후 다시 시도해주세요.")
            elif status_code == 401:
                st.error("🔑 [인증 실패] 유효하지 않은 토큰입니다. 설정을 확인하세요.")
            else:
                st.error(f"🌐 [서버 오류] HTTP {status_code} 에러가 발생했습니다.")
        except Exception as e:
            st.error(f"❌ [오류] {str(e)}")
        return None

    @staticmethod
    def verify_token(token: str) -> Tuple[bool, str]:
        """토큰 유효성 검사"""
        api_url = "https://huggingface.co/api/whoami-v2"
        headers = {"Authorization": f"Bearer {token.strip()}"}
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return True, response.json().get("name", "User")
            return False, "토큰이 유효하지 않습니다."
        except Exception as e:
            return False, f"연결 오류: {str(e)}"

# --- [2. 세션 상태 및 초기화] ---

def initialize_session():
    defaults = {
        "authenticated": False,
        "hf_token": "",
        "img_history": [],
        "novel_draft": "",
        "playlists_dict": {"기본 재생목록": []},
        "current_playlist_name": "기본 재생목록",
        "current_track_index": 0,
        "theme": "Default"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- [3. 메인 화면 렌더링 함수들] ---

def render_image_generation_hub():
    st.header("🎨 Image Generation Hub")
    sub_hf, sub_ext, sub_comfy = st.tabs(["☁️ Hugging Face", "🌐 외부 사이트", "💻 ComfyUI (Local)"])
    
    with sub_hf:
        prompt = st.text_input("그림 묘사 (영문)", key="hf_p")
        if st.button("Hugging Face 생성 실행"):
            if not st.session_state["hf_token"]:
                st.warning("토큰이 설정되지 않았습니다.")
                return
            gen = HFImageGenerator(st.session_state["hf_token"])
            with st.spinner("AI가 그리는 중..."):
                img = gen.generate(prompt)
                if img:
                    st.session_state["img_history"].insert(0, {"image": img, "prompt": prompt})
                    st.image(img, use_container_width=True)

    with sub_ext:
        st.subheader("🔗 Daily Free Credits Sites")
        c1, c2, c3 = st.columns(3)
        c1.link_button("Civitai", "https://civitai.com/generate", use_container_width=True)
        c2.link_button("SeaArt", "https://www.seaart.ai/", use_container_width=True)
        c3.link_button("Tensor.art", "https://tensor.art/", use_container_width=True)
        with st.expander("📝 나의 계정 수첩"):
            st.text_area("비밀번호 등 메모", placeholder="사이트별 계정 정보")

    with sub_comfy:
        st.info("🏠 집 컴퓨터의 ComfyUI와 연동될 구역입니다. (준비 중)")

def render_audio_manager():
    st.header("🎵 스마트 작업실 오디오 매니저")
    curr_name = st.session_state["current_playlist_name"]
    active_list = st.session_state["playlists_dict"][curr_name]

    # 목록 관리
    with st.expander("📂 재생목록 생성/변경"):
        plist_names = list(st.session_state["playlists_dict"].keys())
        sel = st.selectbox("목록 선택", plist_names, index=plist_names.index(curr_name))
        if sel != curr_name:
            st.session_state["current_playlist_name"] = sel
            st.rerun()
        
        new_name = st.text_input("새 목록 이름")
        if st.button("목록 생성"):
            if new_name and new_name not in st.session_state["playlists_dict"]:
                st.session_state["playlists_dict"][new_name] = []
                st.rerun()

    # 재생 및 추가
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"📻 {curr_name}")
        if active_list:
            idx = st.session_state["current_track_index"]
            track = active_list[idx % len(active_list)]
            st.video(track['url']) if track['type'] == 'youtube' else st.audio(track['url'])
            st.info(f"재생 중: {track['title']}")
        else:
            st.warning("목록이 비었습니다.")

    with col2:
        st.subheader("➕ 곡 추가")
        mode = st.radio("방식", ["YouTube", "Local File"], horizontal=True)
        if mode == "YouTube":
            u, t = st.text_input("URL"), st.text_input("제목")
            if st.button("추가") and u:
                st.session_state["playlists_dict"][curr_name].append({"type": "youtube", "url": u, "title": t})
                st.rerun()
        else:
            f = st.file_uploader("MP3", type=["mp3"])
            if f and st.button("파일 추가"):
                st.session_state["playlists_dict"][curr_name].append({"type": "local", "url": f, "title": f.name})
                st.rerun()

# --- [4. 메인 실행부] ---

def main():
    st.set_page_config(page_title="AI 작업실 PRO", layout="wide")
    initialize_session()
    StyleManager.apply_theme(st.session_state["theme"])

    # 로그인 로직
    if not st.session_state["authenticated"]:
        st.title("🔐 작업실 입장 (HF 인증)")
        token_input = st.text_input("Hugging Face Read Token", type="password")
        if st.button("인증 및 입장"):
            valid, res = HFImageGenerator.verify_token(token_input)
            if valid:
                st.session_state.update({"authenticated": True, "hf_token": token_input})
                st.rerun()
            else: st.error(res)
        st.stop()

    # 사이드바
    with st.sidebar:
        st.title("🌌 COSMOS")
        menu = st.radio("구역 이동", ["🎨 이미지 생성소", "✍️ 스토리 빌더", "📌 창작 리소스", "🎵 작업실 환경"])
        st.divider()
        new_theme = st.selectbox("테마", ["Default", "Retro Arcade", "Cyber Future"], 
                                 index=["Default", "Retro Arcade", "Cyber Future"].index(st.session_state["theme"]))
        if new_theme != st.session_state["theme"]:
            st.session_state["theme"] = new_theme
            st.rerun()
        
        # 보관함
        st.title("📂 보관함")
        if st.session_state["img_history"]:
            for i, item in enumerate(st.session_state["img_history"]):
                with st.expander(f"기록 {i+1}"): st.image(item["image"])

    # 메뉴별 렌더링
    if menu == "🎨 이미지 생성소": render_image_generation_hub()
    elif menu == "🎵 작업실 환경": render_audio_manager()
    elif menu == "✍️ 스토리 빌더":
        st.header("✍️ AI 시나리오 빌더")
        col_w, col_a = st.columns([2, 1])
        with col_w:
            st.session_state["novel_draft"] = st.text_area("메모장", value=st.session_state["novel_draft"], height=500)
        with col_a:
            st.link_button("Gemini", "https://gemini.google.com/app", use_container_width=True)
            st.link_button("ChatGPT", "https://chatgpt.com", use_container_width=True)
    elif menu == "📌 창작 리소스":
        # (기존 서랍형 리소스 코드 생략, 구조 동일)
        st.header("📌 Creative Resources")
        with st.expander("🎨 레퍼런스"): st.link_button("Pinterest", "https://pinterest.com")
        with st.expander("✨ AI 도구"): st.link_button("DeepL", "https://deepl.com")

if __name__ == "__main__":
    main()