"""
베이스 파서 추상 클래스
"""
from abc import ABC, abstractmethod


class BaseParser(ABC):
    """
    쇼핑몰별 파서의 베이스 클래스
    """

    def __init__(self, soup, url=""):
        """
        Args:
            soup: BeautifulSoup 객체
            url: 상품 URL
        """
        self.soup = soup
        self.url = url

    @abstractmethod
    def parse_price(self):
        """
        가격 추출 (숫자만 반환)
        Returns:
            int or None
        """
        pass

    @abstractmethod
    def parse_product_name(self):
        """
        상품명 추출
        Returns:
            str
        """
        pass

    @abstractmethod
    def parse_image(self):
        """
        이미지 URL 추출
        Returns:
            str
        """
        pass

