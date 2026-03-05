"""
쇼핑몰별 가격 파서 구현
"""
import json
import re
from .base_parser import BaseParser
from utils import extract_number_from_price


class CommonParser(BaseParser):
    """
    공통 파서 로직
    """
    def parse_price(self):
        # 공통: JSON-LD 스키마 시도 (가장 정확)
        json_ld = self.soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                data = json.loads(json_ld.text)
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    print(f"공통 파서 추출 성공: {data['offers']['price']}원")
                    return extract_number_from_price(data['offers']['price'])
            except: pass
        return None

    def parse_product_name(self):
        # og:title 우선
        og_title = self.soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]

        # title 태그
        title_tag = self.soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)

        return "상품명을 찾을 수 없습니다"

    def parse_image(self):
        # preload 이미지 우선
        preload_image = self.soup.find("link", attrs={"rel": "preload", "as": "image"})
        if preload_image and preload_image.get("href"):
            return preload_image["href"]

        # og:image
        og_image = self.soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]

        return "https://placehold.co/600x600/f8fafc/2563eb.png?text=No+Image"


class KurlyParser(CommonParser):
    """
    마켓컬리 전용 파서
    """
    def parse_price(self):
        price = super().parse_price()
        if price:
            return price

        # 컬리: 클래스명이 유동적이므로 패턴으로 접근
        price_tag = self.soup.find('span', string=re.compile(r'^[0-9,]+$'))
        if price_tag:
            print(f"추출 성공: {price_tag.text}원")
            return extract_number_from_price(price_tag.text)

        return None


class SsgParser(CommonParser):
    """
    이마트몰 전용 파서
    """
    def parse_price(self):
        price = super().parse_price()
        if price:
            return price

        # 이마트몰: .ssg_price 클래스 타겟
        price_tag = self.soup.select_one('.cdtl_optprice .ssg_price')
        if price_tag:
            print(f"추출 성공: {price_tag.text}원")
            return extract_number_from_price(price_tag.text)

        return None


class OasisParser(CommonParser):
    """
    오아시스 전용 파서
    """
    def parse_price(self):
        price = super().parse_price()
        if price:
            return price

        # 오아시스: .textPrice 내의 b 태그 (실 판매가)
        price_tag = self.soup.select_one('.textPrice > b')
        if price_tag:
            print(f"추출 성공: {price_tag.text}원")
            return extract_number_from_price(price_tag.text)

        return None


def parse_product_info(soup, site_type, url=""):
    """
    쇼핑몰 타입에 따라 적절한 파서를 선택하여 정보 추출

    Args:
        soup: BeautifulSoup 객체
        site_type: 쇼핑몰 타입 ('kurly', 'ssg', 'oasis' 등)
        url: 상품의 URL

    Returns:
        dict: {
            'name': str,
            'price': int or None,
            'image_url': str
        }
    """
    if site_type == "kurly":
        parser = KurlyParser(soup, url)
    elif site_type == "ssg":
        parser = SsgParser(soup, url)
    elif site_type == "oasis":
        parser = OasisParser(soup, url)
    else:
        # 다른 쇼핑몰은 공통 파서 사용
        parser = CommonParser(soup, url)

    return {
        'name': parser.parse_product_name(),
        'price': parser.parse_price(),
        'image_url': parser.parse_image()
    }
