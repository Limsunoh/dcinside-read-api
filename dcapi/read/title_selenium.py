# -*- coding:utf-8 -*-
"""
Selenium을 사용한 디시인사이드 갤러리 글 목록 가져오기
실제 브라우저를 사용하여 봇 차단을 우회합니다.
"""
from bs4 import BeautifulSoup
import re
import time

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium이 설치되지 않았습니다. 'pip install selenium'으로 설치하세요.")


def _extract_post_num(href):
    """링크에서 글 번호를 추출합니다."""
    if not href:
        return None
    # href 예시: /board/view/?id=dcbest&no=1234567&page=1
    # 또는 /board/dcbest/1234567
    match = re.search(r'no=(\d+)', href)
    if match:
        return match.group(1)
    # 모바일 형식: /board/gall_name/1234567
    match = re.search(r'/(\d+)(?:\?|$)', href)
    if match:
        return match.group(1)
    return None


def _get_driver(headless=True):
    """Chrome WebDriver를 생성합니다."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Chrome WebDriver 생성 실패: {e}")
        print("ChromeDriver를 설치하거나 경로를 설정하세요.")
        return None


def _req_selenium(gall_name, page, return_data, driver=None, is_minor_gallery=False):
    """Selenium을 사용하여 글 목록을 가져옵니다."""
    if not SELENIUM_AVAILABLE:
        return_data[page] = []
        return
    
    close_driver = False
    if driver is None:
        driver = _get_driver(headless=True)
        if driver is None:
            return_data[page] = []
            return
        close_driver = True
    
    try:
        # 마이너 갤러리인 경우 바로 마이너 갤러리 URL로 시도
        if is_minor_gallery:
            # 마이너 갤러리 모바일 버전 시도 (HTML 구조가 단순해서 파싱이 쉬움)
            mobile_url = f"https://m.dcinside.com/mgallery/board/{gall_name}?page={page}"
            driver.get(mobile_url)
            time.sleep(2)  # 페이지 로딩 대기
            html = driver.page_source
            
            # 응답이 너무 짧으면 마이너 갤러리 데스크톱 버전 시도
            if len(html) < 1000:
                base_url = "https://gall.dcinside.com/mgallery/board/lists/"
                desktop_url = f"{base_url}?id={gall_name}&page={page}"
                driver.get(desktop_url)
                time.sleep(3)  # 페이지 로딩 대기
                html = driver.page_source
        else:
            # 일반 갤러리 모바일 버전 시도 (HTML 구조가 단순해서 파싱이 쉬움)
            mobile_url = f"https://m.dcinside.com/board/{gall_name}?page={page}"
            driver.get(mobile_url)
            time.sleep(2)  # 페이지 로딩 대기
            html = driver.page_source
            
            # 응답이 너무 짧으면 일반 갤러리 데스크톱 버전 시도
            if len(html) < 1000:
                base_url = "https://gall.dcinside.com/board/lists/"
                desktop_url = f"{base_url}?id={gall_name}&page={page}"
                driver.get(desktop_url)
                time.sleep(3)  # 페이지 로딩 대기
                html = driver.page_source
        
        if len(html) < 1000:
            print(f"페이지 {page} 응답이 너무 짧습니다 ({len(html)}바이트).")
            return_data[page] = []
            return
        
        soup = BeautifulSoup(html, 'lxml')
        
        # 모바일 버전 파싱 시도
        list_title1 = soup.find_all('a', href=re.compile(r'/board/' + gall_name + r'/\d+'))
        
        # 데스크톱 버전 파싱 시도
        if not list_title1:
            list_title1 = soup.find_all('td', {'class': 'gall_tit ub-word'})
        if not list_title1:
            list_title1 = soup.find_all('td', class_=lambda x: x and 'gall_tit' in str(x))
        if not list_title1:
            list_title1 = soup.find_all('a', href=re.compile(r'/board/view/'))
        
        temp = []
        for item in list_title1:
            try:
                # item이 이미 a 태그인 경우
                if item.name == 'a':
                    a_tag = item
                else:
                    a_tag = item.find('a')
                
                if a_tag:
                    title = a_tag.getText().strip()
                    href = a_tag.get('href', '')
                    
                    # href에서 직접 글 번호 추출 시도
                    post_num = _extract_post_num(href)
                    
                    # 추출 실패 시 다른 방법 시도
                    if not post_num:
                        # 모바일 형식: /board/gall_name/post_num
                        if '/board/' in href:
                            parts = href.split('/')
                            for i, part in enumerate(parts):
                                if part == gall_name and i + 1 < len(parts):
                                    next_part = parts[i + 1]
                                    # 숫자만 있는지 확인
                                    if next_part.isdigit():
                                        post_num = next_part
                                        break
                    
                    # 여전히 실패하면 URL 파라미터에서 추출
                    if not post_num and 'no=' in href:
                        import urllib.parse
                        parsed = urllib.parse.urlparse(href)
                        params = urllib.parse.parse_qs(parsed.query)
                        if 'no' in params:
                            post_num = params['no'][0]
                    
                    # 썸네일 이미지 찾기
                    thumbnail = None
                    # 같은 행에서 이미지 찾기
                    if item.name != 'a':
                        # td 요소인 경우 부모 행에서 이미지 찾기
                        row = item.find_parent('tr')
                        if row:
                            img_tag = row.find('img')
                            if img_tag:
                                img_src = img_tag.get('src', '') or img_tag.get('data-src', '') or img_tag.get('data-original', '')
                                if img_src:
                                    # 상대 경로를 절대 경로로 변환
                                    if img_src.startswith('//'):
                                        thumbnail = 'http:' + img_src
                                    elif img_src.startswith('/'):
                                        thumbnail = 'http://gall.dcinside.com' + img_src
                                    elif img_src.startswith('http'):
                                        thumbnail = img_src
                                    # 로딩 이미지 제외
                                    if thumbnail and 'loading' not in thumbnail.lower():
                                        pass  # 썸네일로 사용
                                    else:
                                        thumbnail = None
                    
                    if title and post_num:
                        post_data = {
                            'title': title,
                            'post_num': post_num
                        }
                        if thumbnail:
                            post_data['thumbnail'] = thumbnail
                        temp.append(post_data)
            except (AttributeError, IndexError, TypeError):
                continue
        
        if temp:
            return_data[page] = temp
        else:
            return_data[page] = []
            
    except Exception as e:
        print(f"페이지 {page} Selenium 오류: {e}")
        return_data[page] = []
    finally:
        if close_driver and driver:
            driver.quit()


def main(gall_name, start_page=1, end_page=1, headless=True, reuse_driver=True, is_minor_gallery=False):
    """
    Selenium을 사용하여 갤러리의 글 목록을 가져옵니다.

    Args:
        gall_name: 갤러리 영문 이름 (예: 'dcbest', 'programming')
        start_page: 시작 페이지 (기본값: 1)
        end_page: 마지막 페이지 (기본값: 1)
        headless: 헤드리스 모드 사용 여부 (기본값: True)
        reuse_driver: 드라이버 재사용 여부 (기본값: True)
        is_minor_gallery: 마이너 갤러리 여부 (기본값: False)

    Returns:
        dict: {페이지번호: [{'title': '제목', 'post_num': '글번호'}, ...]}

    Example:
        data = main("dcbest", 1, 3)
        # {1: [{'title': '제목1', 'post_num': '1234567'}, ...],
        #  2: [...], 3: [...]}
    """
    if not SELENIUM_AVAILABLE:
        print("Selenium을 사용할 수 없습니다.")
        return {}
    
    start = start_page
    end = end_page + 1
    return_data = {}
    
    driver = None
    if reuse_driver:
        driver = _get_driver(headless=headless)
        if driver is None:
            return {}
    
    try:
        for i in range(start, end):
            _req_selenium(gall_name, i, return_data, driver, is_minor_gallery=is_minor_gallery)
            # 요청 간격을 두어 봇 차단 방지 (마지막 페이지 제외)
            if i < end - 1:
                time.sleep(2)  # 2초 대기
    finally:
        if driver:
            driver.quit()
    
    return return_data

