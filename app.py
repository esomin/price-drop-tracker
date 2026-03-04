import streamlit as st
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
# 🌐 Selenium 크롤러 함수
# ==========================================
def create_driver():
    """Headless Chrome WebDriver를 생성합니다."""
    options = Options()
    options.add_argument("--headless=new")           # 헤드리스 모드 (화면 없이 실행)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # 실제 사용자처럼 보이도록 User-Agent 설정
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # navigator.webdriver 속성을 숨겨 봇 탐지 우회
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )
    return driver


def fetch_product_info(url: str) -> dict:
    """
    Selenium으로 URL에 접속하여 상품 정보(이름, 이미지)를 추출합니다.
    JavaScript로 렌더링되는 동적 사이트도 처리합니다.
    """
    driver = create_driver()
    try:
        driver.get(url)

        # 페이지가 어느 정도 로드될 때까지 대기 (최대 10초)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # JS 렌더링을 위해 추가 대기
        time.sleep(2)

        # --- og:title로 상품명 추출 ---
        extracted_name = "상품명을 찾을 수 없습니다."
        try:
            og_title = driver.find_element(By.XPATH, "//meta[@property='og:title']")
            content = og_title.get_attribute("content")
            if content:
                extracted_name = content
        except Exception:
            # og:title이 없으면 <title> 태그로 대체
            try:
                extracted_name = driver.title or extracted_name
            except Exception:
                pass

        # --- og:image로 이미지 추출 ---
        extracted_image = "https://placehold.co/600x600/f8fafc/2563eb.png?text=No+Image"
        try:
            og_image = driver.find_element(By.XPATH, "//meta[@property='og:image']")
            src = og_image.get_attribute("content")
            if src:
                extracted_image = src
        except Exception:
            pass

        return {
            "name": extracted_name,
            "image_url": extracted_image,
        }

    finally:
        driver.quit()  # 반드시 드라이버 종료


# ==========================================
# (A) 헤더 및 입력 섹션
# ==========================================
st.markdown("<h1 style='text-align: center;'>Price DropTracker</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header' style='text-align: center;'>어느 쇼핑몰이든 링크만 넣으면 가격 추적을 시작합니다.</p>", unsafe_allow_html=True)

input_col, btn_col = st.columns([7, 1], gap="small", vertical_alignment="bottom")

with input_col:
    url_input = st.text_input(
        "상품 URL 입력", 
        placeholder="https://... (추적할 상품의 링크를 붙여넣으세요)",
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
    st.markdown(f"#### 📡 실시간 추적 대시보드 (총 {num_products}개 상품)")
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