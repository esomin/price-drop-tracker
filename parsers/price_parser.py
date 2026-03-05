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
        # 방법 1: JSON-LD 스키마 시도 (가장 정확)
        json_ld = self.soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                data = json.loads(json_ld.text)

                # 케이스 A: {"@type": "Product", ...} 형태
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    print(f"공통 파서 추출 성공 (JSON-LD A): {data['offers']['price']}원")
                    return extract_number_from_price(data['offers']['price'])

                # 케이스 B: {"@graph": [...]} 형태
                if isinstance(data, dict):
                    graph = data.get('@graph')
                elif isinstance(data, list):
                    graph = data

                if graph:
                    for item in graph:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            offers = item.get('offers', {})
                            price = offers.get('price') if isinstance(offers, dict) else None
                            if price:   
                                print(f"공통 파서 추출 성공 (JSON-LD @graph): {price}원")
                                return extract_number_from_price(price)
            except: pass
        # 방법 2: 특정 클래스 조건 태그 우선 탐색
        price_num_pattern = re.compile(r'^[0-9,]+$')
        # .price 태그의 숫자 자식
        for parent in self.soup.find_all(class_='price'):
            for tag in parent.find_all():
                text = tag.get_text(strip=True)
                if price_num_pattern.match(text):
                    price_val = extract_number_from_price(text)
                    if price_val and price_val >= 100:
                        print(f"공통 파서 추출 성공 (price 하위 태그): {text}원")
                        return price_val

        # 방법 3: 일반 태그 텍스트 탐색 (span, b, h2, p, strong, em)
        for tag in self.soup.find_all(['span', 'b', 'h2', 'p', 'strong', 'em']):
            text = tag.get_text(strip=True)
            if price_num_pattern.match(text):
                price_val = extract_number_from_price(text)
                if price_val and price_val >= 100:
                    print(f"공통 파서 추출 성공 (태그 텍스트): {text}원")
                    return price_val

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


def parse_product_info(soup, site_type="", url=""):
    """
    쇼핑몰 타입에 관계없이 공통 파서를 사용하여 정보 추출

    Args:
        soup: BeautifulSoup 객체
        site_type: 쇼핑몰 타입 (현재 사용 안함, 호환성을 위해 유지)
        url: 상품의 URL

    Returns:
        dict: {
            'name': str,
            'price': int or None,
            'image_url': str
        }
    """
    parser = CommonParser(soup, url)

    return {
        'name': parser.parse_product_name(),
        'price': parser.parse_price(),
        'image_url': parser.parse_image()
    }
