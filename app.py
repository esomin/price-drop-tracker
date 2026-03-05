import streamlit as st
import time
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from utils import get_site_type, format_price
from parsers import parse_product_info

# 테마 설정
st.set_page_config(
    page_title="Grocery Price Tracker",
    page_icon="🍏",
    layout="wide"
)

primary_color = "#2563eb"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {{
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
    }}
    .stApp h1 {{
        color: #1e293b;
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
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
        transition: box-shadow 0.2s, transform 0.2s;
        margin-bottom: 15px;
        cursor: pointer;
    }}
    .product-card:hover {{
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
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

    /* 상세 페이지 스타일 */
    .detail-img-container {{
        width: 100%;
        max-height: 420px;
        overflow: hidden;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
    }}
    .detail-img {{
        width: 100%;
        max-height: 420px;
        object-fit: contain;
    }}
    .detail-site-badge {{
        display: inline-block;
        background-color: #dbeafe;
        color: #1d4ed8;
        font-size: 0.85em;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        margin-bottom: 16px;
        letter-spacing: 0.5px;
    }}
    .detail-product-title {{
        font-size: 1.4em;
        font-weight: 700;
        color: inherit;
        line-height: 1.5;
        margin-bottom: 20px;
    }}
    .detail-info-wrapper {{
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        min-height: 360px;
    }}
    .detail-info-top {{
        flex: 1;
    }}
    .detail-price-tag {{
        font-size: 2.2em;
        font-weight: 900;
        color: #ef4444;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }}
    .detail-price-label {{
        font-size: 0.85em;
        color: #94a3b8;
        margin-bottom: 28px;
        font-weight: 500;
    }}
    .buy-btn {{
        display: block;
        width: 100%;
        padding: 16px;
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white !important;
        text-align: center;
        border-radius: 12px;
        font-size: 1.05em;
        font-weight: 700;
        text-decoration: none !important;
        transition: all 0.2s ease;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
        margin-bottom: 12px;
    }}
    .buy-btn:hover {{
        background: linear-gradient(135deg, #1d4ed8, #1e40af);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.55);
        transform: translateY(-1px);
    }}
    .graph-section {{
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 32px 24px;
        background: #f8fafc;
        margin-top: 32px;
        text-align: center;
    }}
    .graph-section-title {{
        font-size: 1.1em;
        font-weight: 700;
        color: #334155;
        margin-bottom: 8px;
        text-align: left;
    }}
    .graph-placeholder {{
        color: #94a3b8;
        font-size: 0.95em;
        padding: 48px 0;
    }}
    .graph-placeholder-icon {{
        font-size: 3em;
        margin-bottom: 12px;
    }}
    </style>
    """, unsafe_allow_html=True)

# 💾 Session State 초기화
if 'products' not in st.session_state:
    st.session_state.products = []

if 'selected_product_id' not in st.session_state:
    st.session_state.selected_product_id = None


# ==========================================
# 상세 페이지 렌더링 함수
# ==========================================
def render_detail_page(product):
    # 뒤로가기 버튼
    back_col, _ = st.columns([1, 6])
    with back_col:
        if st.button("← 목록으로", key="back_btn"):
            st.session_state.selected_product_id = None
            st.rerun()

    st.markdown("---")

    img_col, info_col = st.columns([1, 1], gap="large")

    with img_col:
        st.markdown(f"""
            <div class="detail-img-container">
                <img src="{product['image_url']}" class="detail-img" alt="상품 이미지">
            </div>
        """, unsafe_allow_html=True)

    with info_col:
        st.markdown(f"""
            <div class="detail-info-wrapper">
                <div class="detail-info-top">
                    <span class="detail-site-badge">{product['site_name']}</span>
                    <p class="detail-product-title">{product['name']}</p>
                    <p class="detail-price-tag">{product['current_price']}</p>
                    <p class="detail-price-label">현재 추적 가격</p>
                </div>
                <div>
                    <a href="{product['original_url']}" target="_blank" class="buy-btn">
                        제품 구매하러 가기
                    </a>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 가격 변동 그래프 영역
    st.markdown("""
        <div class="graph-section">
            <p class="graph-section-title">가격 변동 추이</p>
            <div class="graph-placeholder">
                <div class="graph-placeholder-icon">📉</div>
                <p>아직 축적된 가격 데이터가 없습니다.<br>가격 추적이 시작되면 여기에 그래프가 표시됩니다.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)


# ==========================================
# 상세 페이지 OR 목록 페이지 분기
# ==========================================
if st.session_state.selected_product_id is not None:
    # 선택된 상품 찾기
    selected = next(
        (p for p in st.session_state.products if p['id'] == st.session_state.selected_product_id),
        None
    )
    if selected:
        st.markdown("<h1 style='text-align: center;'>Grocery Price Tracker</h1>", unsafe_allow_html=True)
        render_detail_page(selected)
    else:
        st.session_state.selected_product_id = None
        st.rerun()

else:
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
    with st.expander("추적 가능한 쇼핑몰을 확인하세요"):
        st.markdown("""
| 쇼핑몰 구분 | 사이트명 | 공식 웹사이트 주소 (URL) |
| :--- | :--- | :--- |
| 신선식품 전문 | 마켓컬리 | https://www.kurly.com |
| 신선식품 전문 | 오아시스마켓 | https://www.oasis.co.kr |
| 대형마트/통합 | 이마트몰 | https://emart.ssg.com |
| 대형마트/통합 | 홈플러스 | https://mfront.homeplus.co.kr |
| 대형마트/통합 | 롯데마트 (제타플렉스) | https://www.lottemart.com |
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
                    response = requests.get(
                                url_val,
                                impersonate="chrome120", # 크롬 브라우저와 똑같은 지문 생성
                                timeout=10
                            )
                    response.raise_for_status() # 오류 발생 시 except 블록으로 이동

                    # 3. HTML 파싱
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # 4. 쇼핑몰 타입 식별
                    site_type = get_site_type(url_val)

                    # 5. 파서를 통해 상품 정보 추출
                    product_info = parse_product_info(soup, site_type, url_val)

                    extracted_name = product_info['name']
                    extracted_image = product_info['image_url']
                    extracted_price = product_info['price']

                    # 6. 가격 포맷팅
                    formatted_price = format_price(extracted_price)

                    # 7. 세션 상태에 저장
                    new_id = len(st.session_state.products) + 1
                    real_product = {
                        "id": new_id,
                        "site_name": domain.upper(),
                        "name": extracted_name,
                        "image_url": extracted_image,
                        "original_url": url_val,
                        "current_price": formatted_price,
                        "price_number": extracted_price  # 숫자값 저장 (향후 가격 비교/정렬 용)
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
                    # 상품 카드 HTML
                    st.markdown(f"""
                        <div class="product-card" id="card-{product['id']}">
                            <span class="site-badge">{product['site_name']}</span>
                            <div class="img-container">
                                <img src="{product['image_url']}" class="product-img" alt="상품 이미지">
                            </div>
                            <p class="product-title" title="{product['name']}">{product['name']}</p>
                            <p class="price-tag">{product['current_price']}</p>
                        </div>
                    """, unsafe_allow_html=True)

                    # 상세 페이지 이동 버튼 (카드 바로 아래)
                    if st.button(
                        "자세히 보기 →",
                        key=f"detail_btn_{product['id']}",
                        use_container_width=True
                    ):
                        st.session_state.selected_product_id = product['id']
                        st.rerun()
                    
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
    st.session_state.selected_product_id = None
    st.rerun()