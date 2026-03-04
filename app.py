import streamlit as st
import time
import random
import os
import ssl
import certifi
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 🔐 macOS Python SSL 인증서 문제 해결
# Python 3.13 + macOS venv 환경에서 certifi 인증서를 명시적으로 지정
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import undetected_chromedriver as uc

# 🎨 테마 설정
st.set_page_config(
    page_title="Price Drop Tracker",
    page_icon="📊",
    layout="wide"
)

primary_color = "#2563eb"

st.markdown(f"""
    <style>
    .stApp h1 {{
        color: #1e293b;
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        font-weight: 800;
    }}
    .sub-header {{
        color: #64748b;
        font-size: 1.1em;
        margin-bottom: 2rem;
    }}
    div[data-testid="stTextInput"] label {{
        color: #334155;
        font-weight: 600;
    }}
    .stButton>button {{
        background-color: {primary_color};
        color: white;
        border-radius: 6px;
        font-weight: bold;
        border: none;
        transition: all 0.2s ease-in-out;
    }}
    .stButton>button:hover {{
        background-color: #1d4ed8;
        transform: translateY(-1px);
    }}
    
    /* 통합 상품 카드 스타일 */
    .product-card {{
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        background-color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: box-shadow 0.2s;
        margin-bottom: 15px;
    }}
    .product-card:hover {{
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }}
    .img-container {{
        width: 100%;
        height: 200px; 
        overflow: hidden;
        border-radius: 8px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #f8fafc;
    }}
    .product-img {{
        width: 100%;
        height: 100%;
        object-fit: contain; 
    }}
    .site-badge {{
        display: inline-block;
        background-color: #f1f5f9;
        color: #475569;
        font-size: 0.75em;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        margin-bottom: 8px;
    }}
    .product-title {{
        font-size: 0.95em;
        font-weight: 600;
        color: #0f172a;
        margin: 0 0 8px 0;
        display: -webkit-box;
        -webkit-line-clamp: 2; 
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.4;
        height: 2.8em;
    }}
    .price-tag {{
        font-size: 1.1em;
        font-weight: 800;
        color: #ef4444; 
        margin: 0;
    }}
    </style>
    """, unsafe_allow_html=True)

# 💾 Session State 초기화
if 'products' not in st.session_state:
    st.session_state.products = []


# ==========================================
# 🌐 undetected-chromedriver 크롤러 함수
# ==========================================
def create_driver():
    """
    undetected-chromedriver로 실제 Chrome을 실행합니다.
    headless 모드는 쿠팡(Cloudflare)·네이버에서 탐지되므로
    비헤드리스(headless=False) + 창 최소화로 우회합니다.
    """
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Chrome 145와 일치하는 실제 User-Agent
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    )
    # 비헤드리스 모드 (headless는 Cloudflare·Naver 탐지에 걸림)
    driver = uc.Chrome(options=options, headless=False, use_subprocess=True, version_main=145)

    # 창을 즉시 최소화 (UI 방해 최소화)
    driver.minimize_window()

    # ── 스텔스 JS 패치 ──────────────────────────────────────────
    # headless가 아니어도 webdriver 잔재·fingerprint를 추가로 숨김
    stealth_js = """
        // navigator.webdriver 완전 제거
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

        // 플러그인 목록 채우기 (headless는 보통 0개)
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Plugin' },
                { name: 'Chrome PDF Viewer' },
                { name: 'Native Client' }
            ]
        });

        // 언어 설정 (한국어 환경처럼)
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ko-KR', 'ko', 'en-US', 'en']
        });

        // window.chrome 객체 존재 확인 (headless에서 없으면 탐지됨)
        if (!window.chrome) {
            window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){} };
        }

        // Notification 권한 쿼리 우회
        const _origQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (params) =>
            params.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : _origQuery(params);

        // iframe 안에서도 webdriver 속성 숨김
        const _origGetter = HTMLIFrameElement.prototype.__lookupGetter__('contentWindow');
        Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
            get: function() {
                const win = _origGetter.call(this);
                if (win) {
                    try {
                        Object.defineProperty(win.navigator, 'webdriver', { get: () => undefined });
                    } catch(e) {}
                }
                return win;
            }
        });
    """
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": stealth_js}
    )
    return driver


def human_scroll(driver):
    """봇처럼 보이지 않도록 자연스러운 스크롤 동작을 수행합니다."""
    total_height = driver.execute_script("return document.body.scrollHeight")
    scroll_step = random.randint(300, 600)
    current = 0
    while current < min(total_height, 2000):
        current += scroll_step
        driver.execute_script(f"window.scrollTo(0, {current});")
        time.sleep(random.uniform(0.2, 0.5))
    driver.execute_script("window.scrollTo(0, 0);")


def wait_for_page_ready(driver, timeout=20):
    """페이지가 완전히 로드될 때까지 대기합니다."""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def extract_og_tags(driver):
    """og:title, og:image 메타 태그를 추출합니다."""
    name = None
    image = None
    try:
        el = driver.find_element(By.XPATH, "//meta[@property='og:title']")
        name = el.get_attribute("content") or None
    except Exception:
        pass
    if not name:
        try:
            name = driver.title or None
        except Exception:
            pass

    try:
        el = driver.find_element(By.XPATH, "//meta[@property='og:image']")
        image = el.get_attribute("content") or None
    except Exception:
        pass

    return name, image


def fetch_product_info(url: str) -> dict:
    """
    undetected-chromedriver로 URL에 접속하여 상품 정보를 추출합니다.
    Naver, Coupang 등 강력한 봇 탐지 사이트를 처리합니다.
    """
    driver = create_driver()
    NO_IMAGE = "https://placehold.co/600x600/f8fafc/2563eb.png?text=No+Image"

    try:
        # 본 상품 URL 접속
        driver.get(url)
        wait_for_page_ready(driver, timeout=25)

        # JS 렌더링 + Cloudflare/봇 감지 해제 대기
        time.sleep(random.uniform(3, 5))
        human_scroll(driver)
        time.sleep(random.uniform(1, 2))

        # og 태그 추출
        extracted_name, extracted_image = extract_og_tags(driver)

        return {
            "name": extracted_name or "상품명을 찾을 수 없습니다.",
            "image_url": extracted_image or NO_IMAGE,
        }

    finally:
        driver.quit()


# ==========================================
# (A) 헤더 및 입력 섹션
# ==========================================
st.markdown("<h1 style='text-align: center;'>Price DropTracker</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header' style='text-align: center;'>링크를 붙여 넣으면 가격 추적을 시작합니다.</p>", unsafe_allow_html=True)

input_col, btn_col = st.columns([7, 1], gap="small", vertical_alignment="bottom")

with input_col:
    url_input = st.text_input(
        "상품 URL 입력", 
        placeholder="https://...",
        label_visibility="collapsed"
    )

with btn_col:
    add_btn = st.button("추가하기", use_container_width=True)

# "추가하기" 버튼 로직 (Selenium 크롤링 엔진)
if add_btn and url_input:
    if url_input.startswith("http://") or url_input.startswith("https://"):
        domain = urlparse(url_input).netloc.replace("www.", "").replace("m.", "").split(".")[0]

        with st.spinner('Selenium으로 페이지를 불러오는 중... (10~20초 소요될 수 있습니다)'):
            try:
                product_info = fetch_product_info(url_input)

                new_id = len(st.session_state.products) + 1
                real_product = {
                    "id": new_id,
                    "site_name": domain.upper(),
                    "name": product_info["name"],
                    "image_url": product_info["image_url"],
                    "original_url": url_input,
                    "current_price": "가격 수집 대기중..."  # 다음 단계에서 구현할 부분
                }

                st.session_state.products.append(real_product)
                st.rerun()

            except Exception as e:
                st.error(f"데이터 추출 중 오류가 발생했습니다: {e}")
    else:
        st.error("올바른 URL 형식(http:// 또는 https://)을 입력해주세요.")


# ==========================================
# (B) 통합 모니터링 대시보드 (격자 리스트)
# ==========================================
num_products = len(st.session_state.products)

if num_products > 0:
    st.markdown(f"#### 실시간 추적 대시보드 (총 {num_products}개 상품)")
    st.divider()
    
    cols_per_row = 4
    
    for i in range(0, num_products, cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j in range(cols_per_row):
            product_index = i + j
            if product_index >= num_products:
                break
                
            product = st.session_state.products[product_index]
            
            with cols[j]:
                st.markdown(f"""
                    <div class="product-card">
                        <span class="site-badge">{product['site_name']}</span>
                        <div class="img-container">
                            <img src="{product['image_url']}" class="product-img" alt="상품 이미지">
                        </div>
                        <p class="product-title" title="{product['name']}">{product['name']}</p>
                        <p class="price-tag">{product['current_price']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
else:
    st.divider()
    st.info("즐겨 찾는 쇼핑몰의 상품 링크를 복사해서 넣어보세요.")

st.sidebar.title("메뉴")
st.sidebar.markdown("- 통합 대시보드")
st.sidebar.markdown("- 가격 하락 알림 설정")
st.sidebar.markdown("- 카테고리별 모아보기")

st.sidebar.divider()
if st.sidebar.button("초기화 (모든 데이터 지우기)"):
    st.session_state.products = []
    st.rerun()