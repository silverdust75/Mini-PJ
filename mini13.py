import streamlit as st
import requests
import io
from PIL import Image
from huggingface_hub import InferenceClient
from typing import List, Dict, Any, Optional, Tuple
import time  # 상단에 추가
import os
import json
import huggingface_hub
print(f"huggingface_hub 버전: {huggingface_hub.__version__}")
def get_audio_cover(audio_file):
    """MP3 파일에서 커버 이미지를 추출하는 함수"""
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC
    try:
        # 파일 포인터를 처음으로 되돌림
        audio_file.seek(0)
        audio = MP3(audio_file, ID3=ID3)
        for tag in audio.tags.values():
            if isinstance(tag, APIC): # 커버 이미지 태그 확인
                return tag.data
    except Exception:
        pass
    return None # 이미지가 없으면 None 반환

# --- [1. 클래스 기반 모듈화: 유틸리티 및 API 관리] ---

class StyleManager:
    """테마 및 CSS 스타일 적용 클래스"""
    @staticmethod
    def apply_theme(theme_name: str) -> None:
        if theme_name == "Retro Arcade":
            bg_url = "https://raw.githubusercontent.com/silverdust75/Mini-PJ/main/bg2.png"
            icon_off = "https://raw.githubusercontent.com/silverdust75/Mini-PJ/main/nbut.png"
            icon_on = "https://raw.githubusercontent.com/silverdust75/Mini-PJ/main/sbut.png"
            
            st.markdown(f"""
                <style>
                /* 1. 전체 배경 */
                .stApp {{ 
                    background-color: #1e130c !important; 
                    background-image: linear-gradient(rgba(30, 19, 12, 0.8), rgba(30, 19, 12, 0.8)), url('{bg_url}') !important; 
                    background-size: cover !important;
                    background-attachment: fixed !important;
                }}

                /* 2. 알림창 및 컨테이너 스타일 (중복 정리) */
                [data-testid="stNotification"] {{
                    background-color: rgba(30, 19, 12, 0.95) !important;
                    border: 2px solid #d4af37 !important;
                    border-radius: 8px !important;
                    color: #fceabb !important;
                    box-shadow: none !important;
                }}
                [data-testid="stNotification"]::before {{ display: none !important; }}

                /* 3. 텍스트 가독성 */
                h1, h2, h3, .stSubheader {{ color: #fceabb !important; text-shadow: 2px 2px 4px #000 !important; }}
                p, span, label, li {{ color: #d4af37 !important; font-weight: 500 !important; }}

                /* 4. 버튼 및 입력창 (중복 제거 및 통합) */
                div.stButton > button, div.stLinkButton > a, .stTextInput input, .stSelectbox div[data-baseweb="select"] {{ 
                    background-color: rgba(0, 0, 0, 0.7) !important; 
                    color: #d4af37 !important; 
                    border: 1px solid #d4af37 !important; 
                }}
                section[data-testid="stSidebar"] {{ background-color: rgba(15, 10, 5, 0.95) !important; }}
/* 5. Expander(서랍) 디자인 최적화 */
                
/* [1. 서랍 최외곽 컨테이너] */
div[data-testid="stExpander"] {{
    border: 2px solid #d4af37 !important;
    border-radius: 8px !important;
    background-color: rgba(30, 19, 12, 0.95) !important;
    padding: 0px !important;
    overflow: hidden !important;
}}

/* [2. 서랍이 열렸을 때도 동일] */
div[data-testid="stExpander"]:has(details[open]) {{
    background-color: rgba(30, 19, 12, 0.95) !important;
}}

/* [3. 제목 영역: 클릭 범위를 확보하면서 배경은 가리지 않음] */
div[data-testid="stExpander"] summary {{
    background-color: transparent !important;
    padding: 20px 15px !important; 
    margin: 0px !important;
    color: #fceabb !important;
    list-style: none !important;
    display: flex !important;
    align-items: center !important;
    border: none !important;
}}

/* 스트림릿 기본 화살표 숨기기 */
div[data-testid="stExpander"] summary svg {{
    display: none !important;
}}

/* [4. 아이콘 설정 (크기 40px 유지)] */
div[data-testid="stExpander"] summary::before {{
    content: "" !important;
    display: inline-block !important;
    width: 40px !important;
    height: 40px !important;
    margin-right: 15px !important;
    background-image: url('{icon_off}') !important;
    background-size: contain !important;
    background-repeat: no-repeat !important;
    flex-shrink: 0 !important;
}}

div[data-testid="stExpander"] details[open] summary::before {{
    background-image: url('{icon_on}') !important;
}}

/* [5. 서랍 내용 영역] */
div[data-testid="stExpanderDetails"] {{
    background-color: rgba(0, 0, 0, 0.2) !important;
    padding: 20px !important;
    color: #ffffff !important;
    border-top: 1px solid rgba(212, 175, 55, 0.3) !important;
    margin: 0px !important;
}}
                </style>
            """, unsafe_allow_html=True)
        elif theme_name == "Midnight Galaxy":
            Mbg_url = "https://raw.githubusercontent.com/silverdust75/Mini-PJ/main/Mbg.jpg"
            Micon_off = "https://raw.githubusercontent.com/silverdust75/Mini-PJ/main/Micon_off.png"
            Micon_on = "https://raw.githubusercontent.com/silverdust75/Mini-PJ/main/Micon_on.png"
            st.markdown(f"""
                <style>
                /* [2. 배경 설정] 기존 그라데이션 위에 이미지를 합성 (배경 안 깨지게 수정) */
                .stApp {{ 
                    background: linear-gradient(180deg, rgba(5, 11, 26, 0.85) 0%, rgba(10, 25, 49, 0.85) 50%, rgba(26, 60, 90, 0.85) 100%), 
                                url('{Mbg_url}') !important;
                    background-size: cover !important;
                    background-attachment: fixed !important;
                    font-family: 'Inter', 'Nanum Gothic', sans-serif !important;
                }}

                /* [3. 기존 스타일 유지] 원본 코드 그대로 */
                div.stButton > button, div.stLinkButton > a {{ background: rgba(0, 150, 255, 0.15) !important; color: #ffffff !important; border: 1px solid rgba(0, 242, 255, 0.5) !important; border-radius: 12px !important; height: 55px !important; backdrop-filter: blur(10px) !important; font-weight: bold !important; text-shadow: 0 0 8px rgba(0, 242, 255, 0.8) !important; }}
                section[data-testid="stSidebar"] {{ background-color: rgba(5, 11, 26, 0.85) !important; border-right: 1px solid rgba(0, 242, 255, 0.2) !important; }}
                p, span, label, [data-testid="stWidgetLabel"] p {{ color: #b0d4ff !important; }}
                h1, h2, h3 {{ color: #ffffff !important; text-shadow: 0 0 15px rgba(0, 150, 255, 0.6) !important; }}

                /* [4. 서랍(Expander) 및 아이콘 로직] */
                div[data-testid="stExpander"] {{ 
                    border: 1px solid rgba(0, 242, 255, 0.2) !important; 
                    background-color: rgba(5, 11, 26, 0.6) !important; 
                    backdrop-filter: blur(15px) !important;
                }}

                /* 아이콘 삽입 (Retro Arcade와 동일 방식) */
                div[data-testid="stExpander"] summary::before {{
                    content: "" !important;
                    display: inline-block !important;
                    width: 50px !important;
                    height: 40px !important;
                    margin-right: 15px !important;
                    background-image: url('{Micon_off}') !important;
                    background-size: contain !important;
                    background-repeat: no-repeat !important;
                }}
                div[data-testid="stExpander"] details[open] summary::before {{
                    background-image: url('{Micon_on}') !important;
                }}
                div[data-testid="stExpander"] summary svg {{ display: none !important; }}

                /* 나머지 원본 유지 */
                div[data-testid="stExpander"] summary {{ background-color: transparent !important; }}
                div[data-testid="stExpander"] details {{ background-color: transparent !important; }}
                div[data-testid="stExpander"] summary p {{ color: #ffffff !important; text-shadow: 0 0 8px rgba(0, 242, 255, 0.5) !important; }}
                div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] {{ background-color: rgba(0, 0, 0, 0.1) !important; }}
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
            
            # --- [신규 추가: 로컬 자동 저장] ---
            import os
            import datetime
            try:
                if not os.path.exists("outputs"):
                    os.makedirs("outputs")
                # 파일명을 날짜_시간_프롬프트일부.png 로 설정
                safe_prompt = "".join([c for c in prompt[:15] if c.isalnum() or c in (' ', '_')]).rstrip()
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"outputs/gen_{timestamp}_{safe_prompt}.png"
                image.save(filename)
            except Exception as save_error:
                print(f"파일 저장 실패: {save_error}") # 저장 실패해도 이미지는 반환하도록 함
            # ----------------------------------

            return image
        except requests.exceptions.HTTPError as e:
            # ... (기존 429, 401 에러 처리 로직 그대로 유지) ...
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
class ComfyUIManager:        
    def __init__(self, comfyui_url: str, comfyui_path: str):
        self.url = comfyui_url
        self.path = comfyui_path
        self.models_path = os.path.join(comfyui_path, "models", "checkpoints")
        self.loras_path = os.path.join(comfyui_path, "models", "loras")
        self.vae_path = os.path.join(comfyui_path, "models", "vae")
        self.upscale_path = os.path.join(comfyui_path, "models", "upscale_models")
    def get_model_list(self, folder_path: str) -> List[str]:
        """폴더에서 파일 목록 가져오기"""
        try:
            if not os.path.exists(folder_path):
                return []
            files = []
            for file in os.listdir(folder_path):
                if file.endswith(('.safetensors', '.ckpt', '.pt')):
                    files.append(file)
            return sorted(files)
        except Exception as e:
            print(f"파일 목록 가져오기 실패: {e}")
            return []

    def check_connection(self) -> Tuple[bool, str]:
        """ComfyUI 서버 연결 확인"""
        try:
            response = requests.get(f"{self.url}/system_stats", timeout=3)
            if response.status_code == 200:
                return True, "✅ ComfyUI 서버 연결 성공"
            return False, f"❌ 서버 응답 오류: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "❌ ComfyUI 서버에 연결할 수 없습니다. ComfyUI가 실행 중인지 확인하세요."
        except Exception as e:
            return False, f"❌ 연결 오류: {str(e)}"

    def create_workflow(self, config: Dict[str, Any]) -> Dict:
        import random
        user_seed = config.get("seed", 42)
        actual_seed = random.randint(0, 1125899906842624) if user_seed == -1 else int(user_seed)

        ckpt_name = config.get("model")
        if not ckpt_name or ckpt_name == "선택하세요...":
            ckpt_name = "realisticVisionV60B1_v51HyperVAE.safetensors"
        
        # 추가 설정값
        upscale_option = config.get("upscale_model")
        upscale_factor = config.get("upscale_factor", 1.5)
        detailer_strength = config.get("detailer_strength", 0.5)
        
        # 기본 워크플로우 구성
        workflow = {
            "3": {
                "inputs": {
                    "seed": actual_seed,
                    "steps": int(config.get("steps", 20)),
                    "cfg": float(config.get("cfg", 7.0)),
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0, # 디테일러 미사용 시 기본값
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler"
            },
            "4": { "inputs": { "ckpt_name": ckpt_name }, "class_type": "CheckpointLoaderSimple" },
            "5": { "inputs": { "width": int(config.get("width", 512)), "height": int(config.get("height", 512)), "batch_size": 1 }, "class_type": "EmptyLatentImage" },
            "6": { "inputs": { "text": str(config.get("positive_prompt", "")), "clip": ["4", 1] }, "class_type": "CLIPTextEncode" },
            "7": { "inputs": { "text": str(config.get("negative_prompt", "")), "clip": ["4", 1] }, "class_type": "CLIPTextEncode" },
            "8": { "inputs": { "samples": ["3", 0], "vae": ["4", 2] }, "class_type": "VAEDecode" },
            "9": { "inputs": { "filename_prefix": "ComfyUI", "images": ["8", 0] }, "class_type": "SaveImage" }
        }

        if config.get("detailer_model") != "사용 안 함":
            workflow["3"]["inputs"]["denoise"] = detailer_strength
        
        # 3. LoRA 처리 (UI 유지용)
        loras = config.get("loras", [])
        if loras:
            last_model = ["4", 0]
            last_clip = ["4", 1]
            node_id = 100
            for lora in loras:
                l_name = lora.get("name")
                if not l_name or l_name == "선택하세요...":
                    continue
                curr_id = str(node_id)
                workflow[curr_id] = {
                    "inputs": {
                        "lora_name": l_name,
                        "strength_model": float(lora.get("strength", 1.0)),
                        "strength_clip": float(lora.get("strength", 1.0)),
                        "model": last_model,
                        "clip": last_clip
                    },
                    "class_type": "LoraLoader"
                }
                last_model = [curr_id, 0]
                last_clip = [curr_id, 1]
                node_id += 1
            
            workflow["3"]["inputs"]["model"] = last_model
            workflow["6"]["inputs"]["clip"] = last_clip
            workflow["7"]["inputs"]["clip"] = last_clip

        if upscale_option == "Latent Upscale":
            workflow["10"] = {
                "inputs": { "upscale_method": "nearest-exact", "factor": upscale_factor, "samples": ["3", 0] },
                "class_type": "LatentUpscaleBy"
            }
            workflow["8"]["inputs"]["samples"] = ["10", 0]

        return workflow

    def generate_image(self, workflow: Dict) -> Optional[bytes]:
        """워크플로우를 ComfyUI에 전송하고 이미지 생성 (대기 로직 강화 버전)"""
        try:
            # 1. 워크플로우 전송
            prompt_data = {"prompt": workflow}
            response = requests.post(
                f"{self.url}/prompt",
                json=prompt_data,
                timeout=10
            )
            
            if response.status_code != 200:
                st.error(f"워크플로우 전송 실패: {response.status_code}")
                return None
            
            result = response.json()
            prompt_id = result.get("prompt_id")
            
            if not prompt_id:
                st.error("Prompt ID를 받지 못했습니다.")
                return None
            
            # 2. 생성 완료 대기 (최대 10분으로 연장)
            max_wait = 600 
            start_time = time.time()
            
            # 여기가 바로 계속 확인하는 루프입니다!
            while time.time() - start_time < max_wait:
                try:
                    history_response = requests.get(f"{self.url}/history/{prompt_id}", timeout=5)
                    if history_response.status_code == 200:
                        history = history_response.json()
                        
                        if prompt_id in history:
                            outputs = history[prompt_id].get("outputs", {})
                            for node_id, node_output in outputs.items():
                                if "images" in node_output:
                                    image_info = node_output["images"][0]
                                    filename = image_info["filename"]
                                    subfolder = image_info.get("subfolder", "")
                                    
                                    image_url = f"{self.url}/view?filename={filename}"
                                    if subfolder:
                                        image_url += f"&subfolder={subfolder}"
                                    
                                    img_response = requests.get(image_url)
                                    if img_response.status_code == 200:
                                        return img_response.content
                    
                    # [중요] 1초마다 물어보던 것을 5초로 늘려 부하를 줄입니다.
                    time.sleep(5) 
                
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    # 연결이 일시적으로 끊겨도(10048 에러 등) 포기하지 않고 10초 쉽니다.
                    time.sleep(10)
                    continue
        
            st.error("이미지 생성 시간 초과 (10분)")
            return None
        
        except Exception as e:
            st.error(f"이미지 생성 오류: {str(e)}")
            return None
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
        "theme": "Default",
        "novel_history": [],
        "comfyui_loras": []  # 이 줄을 새로 추가해 주세요!
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # --- [3. 메인 화면 렌더링 함수들] ---

def render_image_generation_hub():
    st.header("🎨 Image Generation Hub")
    sub_hf, sub_ext, sub_comfy = st.tabs(["☁️ Hugging Face", "🌐 외부 사이트", "💻 ComfyUI (Local)"])
    
    with sub_hf:
        # --- [복구] 토큰 정보 및 종류 표시 영역 ---
        if st.session_state["hf_token"]:
            # 토큰 유효성 및 사용자 정보 확인
            is_valid, res_msg = HFImageGenerator.verify_token(st.session_state["hf_token"])
            
            with st.expander("🔑 현재 토큰 정보 및 사용량 안내", expanded=False):
                if is_valid:
                    # 사용자 이름 표시 및 API 상태 안내
                    st.success(f"✅ 인증 사용자: {res_msg} (연결됨)")
                    st.info("📊 현재 API 종류: Free Tier (Hugging Face Serverless)")
                else:
                    st.error(f"❌ 토큰 상태: {res_msg}")
                
                st.write("---")
                st.caption("💡 무료 API는 시간당 제한이 있으며 자동 결제는 되지 않으니 안심하세요.")

        current_prompt = st.session_state.get("hf_p", "")

        # 2. 강화 버튼 클릭 시 세션 상태를 먼저 업데이트합니다.
        col_enh1, col_enh2 = st.columns([1, 4])
        with col_enh1:
            if st.button("🪄 강화"):
                if current_prompt:
                    enhancements = "masterpiece, highly detailed, 8k resolution, cinematic lighting, sharp focus, intricate textures"
                    # 위젯이 그려지기 전이므로 안전하게 수정 가능합니다.
                    st.session_state["hf_p"] = f"{current_prompt}, {enhancements}"
                    st.rerun()
                else:
                    st.warning("먼저 단어를 입력하세요!")
        with col_enh2:
            st.caption("💡 단어 입력 후 '강화'를 누르면 상세 묘사가 추가됩니다.")

        # --- [수정 포인트 2: 위젯 선언] ---
        # 이제 업데이트된 세션 값이 value로 자연스럽게 들어갑니다.
        prompt = st.text_input(
            "그림 묘사 (영문)", 
            key="hf_p", 
            placeholder="예: A fantasy landscape, digital art"
        )
        
        # [기존] 생성 버튼 및 로직 (그대로 유지)
        if st.button("Hugging Face 생성 실행", use_container_width=True):
            # ... (기존 생성 및 사용량 안내 코드)
            if not st.session_state["hf_token"]:
                st.warning("토큰이 설정되지 않았습니다. 설정 메뉴에서 입력해주세요.")
                return
            
            gen = HFImageGenerator(st.session_state["hf_token"])
            with st.spinner("AI가 그리는 중... 잠시만 기다려주세요."):
                img = gen.generate(prompt)
                if img:
                    st.session_state["img_history"].insert(0, {"image": img, "prompt": prompt})
                    st.image(img, use_container_width=True)
                    st.success("✅ 생성 완료! 무료 할당량을 사용했습니다.")

    with sub_ext:
        st.subheader("🔗 Daily Free Credits Sites")
        c1, c2, c3 = st.columns(3)
        c1.link_button("Civitai", "https://civitai.com/generate", use_container_width=True)
        c2.link_button("SeaArt", "https://www.seaart.ai/", use_container_width=True)
        c3.link_button("Tensor.art", "https://tensor.art/", use_container_width=True)
        with st.expander("📝 나의 계정 수첩"):
            st.text_area("비밀번호 등 메모", placeholder="사이트별 계정 정보")

    with sub_comfy:
        render_comfyui_interface()

def render_audio_manager():
    st.header("🎵 스마트 작업실 오디오 매니저")
    
    # 세션 상태에 인덱스가 없으면 초기화
    if "current_track_index" not in st.session_state:
        st.session_state["current_track_index"] = 0
    if "loop_mode" not in st.session_state:
        st.session_state["loop_mode"] = "전체 반복" # 전체 반복, 한곡 반복, 반복 안함

    curr_name = st.session_state["current_playlist_name"]
    active_list = st.session_state["playlists_dict"][curr_name]

    # --- [1. 목록 관리 및 설정] ---
    with st.expander("📂 재생목록 생성 및 관리"):
        plist_names = list(st.session_state["playlists_dict"].keys())
        sel = st.selectbox("현재 재생목록 선택", plist_names, index=plist_names.index(curr_name))
        
        if sel != curr_name:
            st.session_state["current_playlist_name"] = sel
            st.session_state["current_track_index"] = 0 # 목록 바뀌면 첫 곡부터
            st.rerun()
        
        col_new1, col_new2 = st.columns([3, 1])
        new_name = col_new1.text_input("새 목록 이름", key="new_plist_input")
        if col_new2.button("목록 생성") and new_name:
            if new_name not in st.session_state["playlists_dict"]:
                st.session_state["playlists_dict"][new_name] = []
                st.success(f"'{new_name}' 목록이 생성되었습니다.")
                st.rerun()

    # --- [2. 메인 레이아웃: 재생기 vs 추가/목록] ---
    col_player, col_list = st.columns([1, 1])

    with col_player:
        st.subheader(f"📻 Now Playing: {curr_name}")
        
        if active_list:
            idx = st.session_state["current_track_index"] % len(active_list)
            track = active_list[idx]

            # --- [신규: 커버 이미지 표시] ---
            if track['type'] == 'local':
                cover_data = get_audio_cover(track['url'])
                if cover_data:
                    st.image(cover_data, width=300)
                else:
                    st.info("🖼️ 앨범 아트가 없는 파일입니다.")
            
            # 오디오/비디오 출력
            if track['type'] == 'youtube':
                st.video(track['url'])
            else:
                st.audio(track['url'])
            
            st.info(f"**재생 중 ({idx + 1}/{len(active_list)}):** {track['title']}")

            # --- [신규: 반복 모드 선택 박스] ---
            loop_m = st.selectbox("🔁 반복 설정", ["전체 반복", "한곡 반복", "반복 안함"], 
                                 index=["전체 반복", "한곡 반복", "반복 안함"].index(st.session_state["loop_mode"]))
            st.session_state["loop_mode"] = loop_m

            # 재생 컨트롤 버튼
            c1, c2, c3 = st.columns(3)
            
            # [이전 곡 로직]
            if c1.button("⏮️ 이전 곡"):
                st.session_state["current_track_index"] = (idx - 1) % len(active_list)
                st.rerun()
            
            if c2.button("🔄 새로고침"):
                st.rerun()

            # [다음 곡 로직 - 반복 모드 반영]
            if c3.button("⏭️ 다음 곡"):
                if st.session_state["loop_mode"] == "한곡 반복":
                    # 인덱스 유지
                    pass 
                elif st.session_state["loop_mode"] == "전체 반복":
                    st.session_state["current_track_index"] = (idx + 1) % len(active_list)
                else: # 반복 안함
                    if idx + 1 < len(active_list):
                        st.session_state["current_track_index"] = idx + 1
                    else:
                        st.warning("마지막 곡입니다.")
                st.rerun()
        else:
            st.warning("재생목록이 비어 있습니다. 오른쪽에 곡을 추가해 주세요.")

    with col_list:
        # 곡 추가 섹션
        st.subheader("➕ 곡 추가")
        mode = st.radio("소스 선택", ["YouTube", "Local File"], horizontal=True)
        
        with st.container(border=True):
            if mode == "YouTube":
                u = st.text_input("YouTube URL", key="yt_url_in")
                t = st.text_input("곡 제목", key="yt_title_in", placeholder="미입력 시 URL로 표시")
                if st.button("목록에 추가", use_container_width=True):
                    if u:
                        title = t if t else u
                        st.session_state["playlists_dict"][curr_name].append({"type": "youtube", "url": u, "title": title})
                        st.rerun()
            else:
                f = st.file_uploader("MP3 파일 선택", type=["mp3"])
                if f and st.button("파일 추가", use_container_width=True):
                    st.session_state["playlists_dict"][curr_name].append({"type": "local", "url": f, "title": f.name})
                    st.rerun()

        # 현재 대기열 확인 및 삭제
        st.subheader("📜 대기열 (Queue)")
        if active_list:
            for i, t in enumerate(active_list):
                q_col1, q_col2 = st.columns([4, 1])
                # 현재 재생 중인 곡은 강조
                label = f"▶️ {t['title']}" if i == st.session_state["current_track_index"] % len(active_list) else t['title']
                q_col1.write(f"{i+1}. {label}")
                if q_col2.button("🗑️", key=f"del_track_{i}"):
                    st.session_state["playlists_dict"][curr_name].pop(i)
                    # 삭제 시 인덱스 보정
                    st.rerun()
        else:
            st.caption("추가된 곡이 없습니다.")
def render_comfyui_interface():
    """ComfyUI 연동 인터페이스"""
    if "comfy_presets" not in st.session_state:
        st.session_state.comfy_presets = {}
    if "comfy_history" not in st.session_state:
        st.session_state.comfy_history = []
    if "comfy_presets" not in st.session_state:
        if os.path.exists("my_presets.json"):
            try:
                with open("my_presets.json", "r", encoding="utf-8") as f:
                    st.session_state.comfy_presets = json.load(f)
            except:
                st.session_state.comfy_presets = {}
        else:
            st.session_state.comfy_presets = {}
    st.header("💻 ComfyUI 로컬 생성")

    # ====== [이 부분을 정확히 아래 내용으로 교체하세요] ======
    COMFYUI_URL = "http://127.0.0.1:8188"
    
    home_path = os.path.expanduser("~")
    normal_desktop = os.path.join(home_path, "Desktop")
    onedrive_desktop = os.path.join(home_path, "OneDrive", "Desktop")
    
    if os.path.exists(onedrive_desktop):
        desktop_path = onedrive_desktop
    else:
        desktop_path = normal_desktop
    
    # 사용자님의 실제 경로: 앞에 r을 꼭 붙여주세요!
    COMFYUI_PATH = os.path.join(desktop_path, "ptu", "ComfyUI_windows_portable_nvidia", "ComfyUI") 
    # ======================================================

    comfyui = ComfyUIManager(COMFYUI_URL, COMFYUI_PATH)

    # 연결 상태 확인
    with st.expander("🔌 ComfyUI 서버 상태", expanded=False):
        if st.button("연결 테스트"):
            is_connected, message = comfyui.check_connection()
            if is_connected:
                st.success(message)
            else:
                st.error(message)
                st.info("💡 ComfyUI를 실행하려면:\n터미널에서 `python main.py --listen` 명령어 실행")
                
    st.divider()
    
    st.subheader("🔍 디테일 및 업스케일 설정")
    col_up, col_det = st.columns(2)

    with col_up:
        st.markdown("**🖼️ Latent 업스케일**")
        upscale_option = st.selectbox("업스케일 사용 여부", ["사용 안 함", "Latent Upscale"], key="comfy_up_use")
        upscale_factor = st.slider("확대 배수", 1.0, 3.0, 1.5, 0.1, key="comfy_up_factor")

    with col_det:
        st.markdown("**✨ 디테일러 설정**")
        # 실제 모델 파일이 있다면 comfyui.get_model_list() 사용 가능
        detailer_option = st.selectbox("디테일러 모델", ["사용 안 함", "Face_Detailer_v1", "Hand_Detailer_v1"], key="comfy_det_use")
        detailer_strength = st.slider("보정 강도 (Denoise)", 0.0, 1.0, 0.4, 0.05, key="comfy_det_strength")

    st.divider()
    
    with st.expander("💾 나만의 설정 레시피 (Presets)", expanded=False):
        p_col1, p_col2 = st.columns([3, 1])
        with p_col1:
            preset_name = st.text_input("프리셋 이름 입력", placeholder="예: 실사 반실사 황금조합", key="new_preset_name")
        with p_col2:
            st.write("") # 간격 맞춤
            if st.button("현재 세팅 저장", use_container_width=True):
                if preset_name:
        # 1. 세션 상태에 데이터 구성
                    current_config = {
                        "model": selected_model,
                        "vae": selected_vae,
                        "loras": st.session_state.comfyui_loras.copy(),
                        "pos": positive_prompt,
                        "neg": negative_prompt,
                        "width": width, "height": height, "steps": steps, "cfg": cfg,
                        "up_use": upscale_option,
                        "up_factor": upscale_factor,
                        "det_use": detailer_option,
                        "det_strength": detailer_strength
                    }
                    
                    # 2. 세션에 저장
                    st.session_state.comfy_presets[preset_name] = current_config
                    
                    # 3. [여기에 추가!] 로컬 파일(JSON)로 영구 저장
                    try:
                        with open("my_presets.json", "w", encoding="utf-8") as f:
                            json.dump(st.session_state.comfy_presets, f, ensure_ascii=False, indent=4)
                        st.success(f"'{preset_name}'이(가) 메모리와 파일에 저장되었습니다!")
                    except Exception as e:
                        st.error(f"파일 저장 중 오류 발생: {e}")
                else:
                    st.warning("이름을 입력해주세요.")

        if st.session_state.comfy_presets:
            selected_p = st.selectbox("저장된 프리셋 불러오기", ["선택하세요..."] + list(st.session_state.comfy_presets.keys()))
            if selected_p != "선택하세요...":
                if st.button("이 프리셋 적용하기"):
                    p = st.session_state.comfy_presets[selected_p]
                    # 이 부분은 st.session_state를 직접 수정하거나 
                    # 위젯의 value에 넣어주는 방식으로 동작하게 됩니다. (아래 팁 참조)
                    st.info(f"'{selected_p}' 설정이 로드되었습니다. (페이지를 다시 로드하거나 생성 시 적용됩니다)")
                    
        st.divider()
    
    if st.button("🎨 이미지 생성", use_container_width=True, type="primary", key="comfyui_generate_btn"):
        # ... (기존 방어 로직 유지) ...
        
        config = {
            "model": selected_model,
            "vae": selected_vae if selected_vae != "Automatic" else None,
            "loras": st.session_state.comfyui_loras,
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg": cfg,
            "seed": seed,
            # [추가된 설정값]
            "upscale_model": upscale_option,
            "upscale_factor": upscale_factor,
            "detailer_model": detailer_option,
            "detailer_strength": detailer_strength
        }
    
    st.divider()

    # 생성 설정
    st.subheader("⚙️ 생성 설정")

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    with col_s1:
        width = st.number_input("Width", 256, 2048, 512, 64, key="comfyui_width")

    with col_s2:
        height = st.number_input("Height", 256, 2048, 512, 64, key="comfyui_height")

    with col_s3:
        steps = st.number_input("Steps", 1, 150, 20, 1, key="comfyui_steps")

    with col_s4:
        cfg = st.number_input("CFG Scale", 1.0, 30.0, 7.0, 0.5, key="comfyui_cfg")

    seed = st.number_input("Seed (-1 = 랜덤)", -1, 999999999, -1, key="comfyui_seed")

    st.divider()
    
    # 모델 선택
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎨 모델 설정")
        models = comfyui.get_model_list(comfyui.models_path)
        
        if models:
            selected_model = st.selectbox("체크포인트 모델", models, key="comfyui_model")
        else:
            st.warning(f"⚠️ 모델을 찾을 수 없습니다.\n경로: {comfyui.models_path}")
            selected_model = None

    with col2:
        st.subheader("🔧 VAE 설정")
        vaes = ["Automatic"] + comfyui.get_model_list(comfyui.vae_path)
        selected_vae = st.selectbox("VAE", vaes, key="comfyui_vae")

    st.divider()

    # LoRA 관리
    st.subheader("✨ LoRA 설정")
    loras_available = comfyui.get_model_list(comfyui.loras_path)

    if not loras_available:
        st.warning(f"⚠️ LoRA를 찾을 수 없습니다.\n경로: {comfyui.loras_path}")

    # 현재 추가된 LoRA 목록 표시
    if st.session_state.comfyui_loras:
        for idx, lora_item in enumerate(st.session_state.comfyui_loras):
            col_l1, col_l2, col_l3 = st.columns([3, 2, 1])
            
            with col_l1:
                # 배경색을 살짝 깔아서 어떤 테마에서든 글자가 잘 보이게 만듭니다.
                st.markdown(f"""
                    <div style="
                        background-color: rgba(0, 0, 0, 0.6); 
                        color: #ffffff; 
                        padding: 8px; 
                        border-radius: 5px; 
                        font-size: 16px; 
                        font-weight: bold;
                        text-align: center;
                    ">
                        LoRA {idx+1}: {lora_item['name']}
                    </div>
                """, unsafe_allow_html=True)
            
            with col_l2:
                new_strength = st.slider(
                    "강도",
                    0.0, 2.0, lora_item['strength'],
                    0.05,
                    key=f"lora_strength_{idx}"
                )
                st.session_state.comfyui_loras[idx]['strength'] = new_strength
            
            with col_l3:
                if st.button("🗑️", key=f"del_lora_{idx}"):
                    st.session_state.comfyui_loras.pop(idx)
                    st.rerun()

    # LoRA 추가
    col_add1, col_add2 = st.columns([3, 1])

    with col_add1:
        if loras_available:
            new_lora = st.selectbox("LoRA 추가", ["선택하세요..."] + loras_available, key="new_lora_select")

    with col_add2:
        st.write("")
        if st.button("➕ 추가"):
            if loras_available and new_lora != "선택하세요...":
                st.session_state.comfyui_loras.append({
                    "name": new_lora,
                    "strength": 0.8
                })
                st.rerun()

    st.divider()

    # 프롬프트 입력
    st.subheader("📝 프롬프트")

    positive_prompt = st.text_area(
        "긍정 프롬프트 (Positive)",
        placeholder="beautiful landscape, high quality, masterpiece",
        height=100,
        key="comfyui_pos_prompt"
    )

    negative_prompt = st.text_area(
        "부정 프롬프트 (Negative)",
        placeholder="bad quality, worst quality, blurry",
        height=100,
        key="comfyui_neg_prompt"
    )

    st.divider()

    # 생성 버튼
    # --- [기존의 중복된 '🎨 이미지 생성' 버튼 블록들을 모두 지우고 아래 하나로 통합하세요] ---
    st.divider()

    if st.button("🎨 이미지 생성", use_container_width=True, type="primary", key="comfyui_final_gen_btn"):
        if not selected_model:
            st.error("모델을 선택해주세요!")
        elif not positive_prompt.strip():
            st.warning("긍정 프롬프트를 입력해주세요!")
        else:
            # 1. 설정값 구성
            config = {
                "model": selected_model,
                "vae": selected_vae if selected_vae != "Automatic" else None,
                "loras": st.session_state.comfyui_loras,
                "positive_prompt": positive_prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "seed": seed,
                "upscale_model": upscale_option,
                "upscale_factor": upscale_factor,
                "detailer_model": detailer_option,
                "detailer_strength": detailer_strength
            }
            
            # 2. 워크플로우 생성
            workflow = comfyui.create_workflow(config)
            
            # 3. 이미지 생성 실행
            with st.spinner("🎨 ComfyUI에서 이미지 생성 중... (최대 5분 소요)"):
                image_bytes = comfyui.generate_image(workflow)
                
                if image_bytes:
                    # 4. 화면 출력 및 저장
                    img = Image.open(io.BytesIO(image_bytes))
                    st.success("✅ 생성 완료!")
                    st.image(img, caption="방금 생성된 이미지", use_container_width=True) # 화면에 즉시 출력
                    
                    # 5. 세션 상태(기록 및 보관함) 업데이트
                    history_data = {
                        "image": img,
                        "time": time.strftime("%H:%M:%S"),
                        "model": selected_model,
                        "positive": positive_prompt,
                        "seed": seed if seed != -1 else "Random"
                    }
                    st.session_state.comfy_history.insert(0, history_data)
                    st.session_state["img_history"].insert(0, {"image": img, "prompt": positive_prompt})
                else:
                    st.error("이미지 데이터를 가져오지 못했습니다. ComfyUI 로그를 확인하세요.")
    # --- [4. 메인 실행부] ---

def main():
    st.set_page_config(page_title="AI 작업실 PRO", layout="wide")
    initialize_session()
    StyleManager.apply_theme(st.session_state["theme"])

    # 로그인 로직 (엔터 키 및 버튼 클릭에만 반응하도록 수정)
    if not st.session_state["authenticated"]:
        st.title("🔐 작업실 입장 (HF 인증)")
        
        # 통합 인증 로직을 담은 폼(Form) 사용: 엔터와 버튼을 깔끔하게 분리
        with st.form("login_form", clear_on_submit=False):
            token_input = st.text_input(
                "Hugging Face Read Token", 
                type="password", 
                placeholder="hf_...",
                key="temp_token_input"
            )
            
            submit_button = st.form_submit_button("인증 및 입장", use_container_width=True)
            
            if submit_button:
                token_val = token_input.strip()
                if token_val:
                    with st.spinner("인증 확인 중..."):
                        valid, res = HFImageGenerator.verify_token(token_val)
                        if valid:
                            st.session_state.update({"authenticated": True, "hf_token": token_val})
                            st.rerun()
                        else:
                            st.error(f"❌ {res}")
                else:
                    st.warning("토큰을 입력해주세요.")
        
        st.stop()

    # 사이드바
    with st.sidebar:
        st.title("🌌 COSMOS")
        menu = st.radio("구역 이동", ["🎨 이미지 생성소", "✍️ 스토리 빌더", "📌 창작 리소스", "🎵 작업실 환경"])
        st.divider()
        new_theme = st.selectbox("테마", ["Default", "Retro Arcade", "Midnight Galaxy"], 
                                index=["Default", "Retro Arcade", "Midnight Galaxy"].index(st.session_state["theme"]))
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
        st.header("✍️ AI 시나리오 빌더 & 멀티모달 스튜디오")
        
        # 1. 상단: AI 프롬프트 강화 도구
        with st.expander("🪄 AI 프롬프트 자동 강화 도구", expanded=False):
            col_in, col_out = st.columns([1, 1])
            with col_in:
                idea_input = st.text_input("간단한 아이디어를 입력하세요", placeholder="예: 우주복을 입은 고양이", key="idea_input_unique")
                if st.button("✨ 상세 묘사 생성 (AI)", use_container_width=True, key="btn_enhance_prompt"):
                    if idea_input:
                        with st.spinner("AI가 멋진 프롬프트를 만드는 중..."):
                            try:
                                from huggingface_hub import InferenceClient
                                
                                client = InferenceClient(
                                    model="meta-llama/Llama-3.2-1B-Instruct",
                                    token=st.session_state["hf_token"]
                                )
                                
                                # 영어로 깔끔한 프롬프트만 출력
                                system_msg = """You are a creative writing assistant. Expand the user's brief idea into a detailed scene description for a novel or story.
Output ONLY the expanded scene description in English. Do not include explanations, introductions, or formatting markers like 'Here's' or 'Prompt:'. Just write the scene directly."""
                                
                                messages = [
                                    {"role": "system", "content": system_msg},
                                    {"role": "user", "content": f"Expand this idea into a vivid scene: {idea_input}"}
                                ]
                                
                                response = client.chat_completion(
                                    messages=messages,
                                    max_tokens=200,
                                    temperature=0.7
                                )
                                
                                enhanced = response.choices[0].message.content.strip()
                                
                                # 불필요한 메타 텍스트 제거
                                unwanted_phrases = [
                                    "Here's a detailed",
                                    "Here's an expanded",
                                    "**Prompt:**",
                                    "**Scene:**",
                                    "Prompt:",
                                    "Scene:",
                                ]
                                
                                # 첫 줄이 메타 텍스트면 제거
                                lines = enhanced.split('\n')
                                cleaned_lines = []
                                
                                for line in lines:
                                    # 불필요한 구문 포함 여부 확인
                                    if any(phrase.lower() in line.lower() for phrase in unwanted_phrases):
                                        continue
                                    # ** 마크다운 제거
                                    line = line.replace('**', '').replace('*', '').strip()
                                    if line:
                                        cleaned_lines.append(line)
                                
                                final_result = '\n'.join(cleaned_lines).strip()
                                
                                # 결과가 너무 짧으면 원본 사용
                                if len(final_result) < 10:
                                    final_result = enhanced.replace('**', '').replace('*', '').strip()
                                
                                st.session_state["enhanced_result"] = final_result
                                st.success("✅ 완료!")
                                
                            except Exception as e:
                                st.error(f"오류: {e}")
                                import traceback
                                st.code(traceback.format_exc())
                    else:
                        st.warning("아이디어를 입력해주세요.")
            
            with col_out:
                if "enhanced_result" in st.session_state:
                    st.success("AI 추천 프롬프트:")
                    st.code(st.session_state["enhanced_result"], language="text")
                    st.caption("위 코드를 복사해서 '이미지 생성소'에 붙여넣으세요!")

        st.divider()

        # 2. 중단: 외부 AI 링크 (서포터즈)
        st.subheader("🤖 AI 서포터즈 파트너")
        ai_cols = st.columns(4)
        with ai_cols[0]: st.link_button("✨ Gemini", "https://gemini.google.com/app", use_container_width=True)
        with ai_cols[1]: st.link_button("💬 ChatGPT", "https://chatgpt.com", use_container_width=True)
        with ai_cols[2]: st.link_button("🍀 Claude", "https://claude.ai", use_container_width=True)
        with ai_cols[3]: st.link_button("⚡ Wrtn", "https://wrtn.ai", use_container_width=True)
        
        st.divider()
# [신규] 🎙️ 음성 아이디어 기록 (외부 서비스)
        st.subheader("🎙️ 음성으로 아이디어 기록하기")
        
        st.warning("⚠️ 음성 인식 기능은 외부 서비스를 이용해주세요.")
        
        st.info("""
**💡 추천 무료 음성 인식 서비스:**

아래 서비스에서 음성을 텍스트로 변환한 후, 
결과를 복사해서 아래 집필 영역에 직접 붙여넣으세요.
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.link_button(
                "🎤 네이버 클로바노트",
                "https://clovanote.naver.com/",
                use_container_width=True
            )
            st.caption("✅ 무료, 한국어 특화, 녹음 파일 업로드 가능")
        
        with col2:
            st.link_button(
                "📝 구글 문서 음성 입력",
                "https://docs.google.com/",
                use_container_width=True
            )
            st.caption("✅ 실시간 음성 입력 (도구 > 음성 입력)")
        
        st.markdown("---")
        st.caption("💡 팁: 클로바노트는 녹음 파일을 업로드하면 자동으로 텍스트로 변환해줍니다.")
            
        st.divider()
        # 3. 하단: 메인 집필 및 분석 영역
        col_w, col_h = st.columns([2, 1])
            # text_area의 현재 값을 임시 변수에 저장
        with col_w:
            st.subheader("📝 집필 영역")
            # 디버깅 정보
            st.caption(f"현재 novel_draft 길이: {len(st.session_state['novel_draft'])} 글자")
            
           # 집필 영역 (일반)
            st.session_state["novel_draft"] = st.text_area(
                "이야기를 그려보세요",
                value=st.session_state["novel_draft"],
                height=450,
                placeholder="장면을 묘사하거나 AI 파트너의 피드백을 바탕으로 글을 써보세요...",
                key="main_novel_editor"
            )
            # 멀티모달 분석 버튼
            if st.button("🖼️ 현재 장면에서 삽화 키워드 추출하기", use_container_width=True, key="btn_extract_keywords"):
                if st.session_state["novel_draft"].strip():
                    with st.spinner("분석 중..."):
                        try:
                            from huggingface_hub import InferenceClient
                            
                            client = InferenceClient(
                                model="meta-llama/Llama-3.2-1B-Instruct",
                                token=st.session_state["hf_token"]
                            )
                            
                            analysis_prompt = f"Extract visual keywords (character, environment, lighting, style) for AI image generation from this story. Answer in English, comma-separated:\n{st.session_state['novel_draft'][:500]}"
                            
                            messages = [
                                {"role": "user", "content": analysis_prompt}
                            ]
                            
                            response = client.chat_completion(
                                messages=messages,
                                max_tokens=100
                            )
                            
                            keywords = response.choices[0].message.content
                            st.session_state["visual_concept"] = keywords
                            st.success("✅ 키워드 추출 완료!")
                            
                        except Exception as e:
                            st.error(f"분석 오류: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                else:
                    st.warning("내용을 입력해야 분석이 가능합니다.")

            if "visual_concept" in st.session_state:
                st.info(f"💡 추천 삽화 컨셉: {st.session_state['visual_concept']}")

            # 저장 및 내보내기 버튼 (중복 ID 해결을 위해 key 추가)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📥 임시 보관함에 저장", use_container_width=True, key="btn_save_to_history"):
                    if st.session_state["novel_draft"].strip():
                        import datetime
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        st.session_state["novel_history"].insert(0, {"time": now, "content": st.session_state["novel_draft"]})
                        st.success("보관함에 저장되었습니다!")
                        st.rerun()
            with c2:
                st.download_button("📄 텍스트 파일로 내보내기", st.session_state["novel_draft"], file_name="my_story.txt", use_container_width=True, key="btn_download_txt")

        with col_h:
            st.subheader("📂 임시 보관함")
            if not st.session_state["novel_history"]:
                st.caption("저장된 기록이 없습니다.")
            else:
                for i, doc in enumerate(st.session_state["novel_history"]):
                    with st.expander(f"📌 {doc['time']}"):
                        st.write(doc['content'][:100] + "..." if len(doc['content']) > 100 else doc['content'])
                        col_l, col_d = st.columns(2)
                        with col_l:
                            if st.button("🔄 불러오기", key=f"load_doc_{i}"):
                                st.session_state["novel_draft"] = doc['content']
                                st.rerun()
                        with col_d:
                            if st.button("🗑️ 삭제", key=f"del_doc_{i}"):
                                st.session_state["novel_history"].pop(i)
                                st.rerun()
    elif menu == "📌 창작 리소스":
        st.header("📌 Creative Resources Hub")
        st.write("각 카테고리를 클릭하면 유용한 사이트 목록이 나타납니다.")

        # 1. 레퍼런스 & 커뮤니티
        with st.expander("🎨 레퍼런스 & 아트 커뮤니티", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("Pinterest", "https://www.pinterest.com/", use_container_width=True)
                st.link_button("Pixiv", "https://www.pixiv.net/", use_container_width=True)
            with col2:
                st.link_button("ArtStation", "https://www.artstation.com/", use_container_width=True)
                st.link_button("Civitai", "https://civitai.com/", use_container_width=True)

        # 2. 고화질 이미지 & 에셋
        with st.expander("📸 고화질 사진 & 에셋"):
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("Unsplash", "https://unsplash.com/", use_container_width=True)
                st.link_button("Pexels", "https://www.pexels.com/ko-kr/", use_container_width=True)
            with col2:
                st.link_button("Pixabay", "https://pixabay.com/", use_container_width=True)
                st.link_button("Flaticon (아이콘)", "https://www.flaticon.com/", use_container_width=True)

        # 3. 인체 구조 & 포즈
        with st.expander("🧍 인체 & 포즈 레퍼런스"):
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("Posemaniacs", "https://www.posemaniacs.com/", use_container_width=True)
                st.link_button("Line of Action (크로키)", "https://line-of-action.com/", use_container_width=True)
            with col2:
                st.link_button("MagicPoser (3D)", "https://magicposer.com/", use_container_width=True)
                st.link_button("Adorkastock", "https://www.adorkastock.com/sketch/", use_container_width=True)

        # 4. 컬러 & 디자인 도구
        with st.expander("🌈 컬러 & 디자인 유틸리티"):
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("Adobe Color", "https://color.adobe.com/", use_container_width=True)
                st.link_button("Coolors", "https://coolors.co/", use_container_width=True)
            with col2:
                st.link_button("눈누 (무료 폰트)", "https://noonnu.cc/", use_container_width=True)
                st.link_button("Canva", "https://www.canva.com/", use_container_width=True)

        # 5. AI 창작 보조 도구
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

if __name__ == "__main__":
    main()