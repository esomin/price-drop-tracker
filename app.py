import streamlit as st
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# 🎨 테마 설정
st.set_page_config(
    page_title="Grocery Price Tracker",
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
# (A) 헤더 및 입력 섹션
# ==========================================
st.markdown("<h1 style='text-align: center;'>Grocery Price Tracker</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header' style='text-align: center;'>브랜드 직영몰 및 공식 쇼핑몰 전용 가격 추적 서비스</p>", unsafe_allow_html=True)

with st.form(key="add_product_form", clear_on_submit=True):
    input_col, btn_col = st.columns([7, 1], gap="small", vertical_alignment="bottom")

    with input_col:
        url_input = st.text_input(
            "상품 URL 입력", 
            placeholder="https://...",
            label_visibility="collapsed"
        )

    with btn_col:
        add_btn = st.form_submit_button("추가하기", use_container_width=True)

st.write("") # 약간의 여백
with st.expander("🔍 추적 가능한 쇼핑몰을 확인하세요"):
    st.markdown("""
| 쇼핑몰 구분 | 사이트명 | 공식 웹사이트 주소 (URL) |
| :--- | :--- | :--- |
| 브랜드 직영몰 | CJ 더마켓 | https://www.cjthemarket.com |
| 브랜드 직영몰 | 오뚜기몰 | https://www.ottogimall.co.kr |
| 브랜드 직영몰 | 동원몰 | https://www.dongwonmall.com |
| 신선식품 전문 | 마켓컬리 | https://www.kurly.com |
| 신선식품 전문 | 오아시스마켓 | https://www.oasis.co.kr |
| 대형마트/통합 | SSG닷컴 (이마트) | https://www.ssg.com |
| 대형마트/통합 | 롯데마트 (제타플렉스) | https://www.lottemart.com |
| 대형마트/통합 | 홈플러스 | https://mfront.homeplus.co.kr |
    """)

# "추가하기" 버튼 로직 (실제 크롤링 엔진 적용)
if add_btn and url_input:
    url_val = url_input
    if url_val.startswith("http://") or url_val.startswith("https://"):
        
        parsed_url = urlparse(url_val)
        domain = parsed_url.netloc.replace("www.", "")
        
        with st.spinner('해당 쇼핑몰에서 상품 정보를 추출하는 중입니다...'):
            try:
                # 1. 봇 차단을 막기 위한 헤더 설정
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                # 2. 실제 해당 URL로 요청 보내기
                response = requests.get(url_val, headers=headers, timeout=5)
                response.raise_for_status() # 오류 발생 시 except 블록으로 이동
                
                # 3. HTML 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 4. og:title 추출
                og_title = soup.find("meta", property="og:title")
                extracted_name = og_title["content"] if og_title else "상품명을 찾을 수 없습니다."
                
                # 5. og:image 추출
                og_image = soup.find("meta", property="og:image")
                extracted_image = og_image["content"] if og_image else "https://placehold.co/600x600/f8fafc/2563eb.png?text=No+Image"
                
                # 6. 세션 상태에 저장
                new_id = len(st.session_state.products) + 1
                real_product = {
                    "id": new_id,
                    "site_name": domain.upper(),
                    "name": extracted_name,
                    "image_url": extracted_image,
                    "original_url": url_val,
                    "current_price": "가격 수집 대기중..." # 다음 단계에서 구현할 부분
                }
                
                st.session_state.products.append(real_product)
                st.rerun()

            except requests.exceptions.RequestException as e:
                st.error("페이지에 접속할 수 없습니다. 링크가 정확한지, 혹은 해당 사이트에서 봇 접근을 차단했는지 확인해주세요.")
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
                    <a href="{product['original_url']}" target="_blank" style="text-decoration: none; color: inherit;">
                        <div class="product-card">
                            <span class="site-badge">{product['site_name']}</span>
                            <div class="img-container">
                                <img src="{product['image_url']}" class="product-img" alt="상품 이미지">
                            </div>
                            <p class="product-title" title="{product['name']}">{product['name']}</p>
                            <p class="price-tag">{product['current_price']}</p>
                        </div>
                    </a>
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