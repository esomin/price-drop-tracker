"""
가격 추출 및 포맷팅 유틸리티
"""
import re
from urllib.parse import urlparse


def extract_number_from_price(price_str):
    """
    가격 문자열에서 숫자만 추출
    예: "29,900원" → 29900
        "₩29,900" → 29900
        "29900" → 29900
    """
    if not price_str:
        return None

    # 숫자와 쉼표만 추출
    numbers = re.sub(r'[^\d]', '', str(price_str))

    if numbers:
        return int(numbers)
    return None


def format_price(price):
    """
    숫자를 가격 포맷으로 변환
    예: 29900 → "29,900원"
    """
    if price is None:
        return "가격 정보 없음"

    try:
        return f"{int(price):,}원"
    except (ValueError, TypeError):
        return "가격 정보 없음"


def get_site_type(url):
    """
    URL에서 쇼핑몰 타입 식별
    """
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "").lower()

    if "kurly.com" in domain:
        return "kurly"
    elif "ssg.com" in domain:
        return "ssg"
    elif "oasis.co.kr" in domain:
        return "oasis"
    elif "homeplus.co.kr" in domain:
        return "homeplus"
    elif "lottemart.com" in domain:
        return "lottemart"
    elif "cjthemarket.com" in domain:
        return "cjthemarket"
    elif "ottogi.okitchen.co.kr" in domain:
        return "ottogi"
    elif "dongwonmall.com" in domain:
        return "dongwon"

    return "unknown"

