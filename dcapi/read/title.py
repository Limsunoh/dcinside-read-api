# -*- coding:utf-8 -*-
import requests
from bs4 import BeautifulSoup
import re
import time

# 해당 갤러리의 제목과 글 번호를 가져와 페이지별로 딕셔너리에 담습니다.
# page is key, value is list of dicts with 'title' and 'post_num'
# gall_name  : 갤러리 영문이름
# start_page : 시작페이지
# end_page : 마지막 페이지

def _extract_post_num(href):
    """링크에서 글 번호를 추출합니다."""
    if not href:
        return None
    # href 예시: /board/view/?id=dcbest&no=1234567&page=1
    match = re.search(r'no=(\d+)', href)
    if match:
        return match.group(1)
    return None


def _req(gall_name, page, return_data):
    user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36")
    _headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "http://gall.dcinside.com/",
    }
    # 세션 사용으로 쿠키 관리
    session = requests.Session()
    
    # 먼저 모바일 버전 시도 (차단이 덜함)
    mobile_url = f"http://m.dcinside.com/board/{gall_name}?page={page}"
    mobile_headers = {
        "User-Agent": ("Mozilla/5.0 (Linux; Android 10; SM-G973F) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.120 Mobile Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9",
    }
    
    try:
        # 모바일 버전 먼저 시도
        req = session.get(url=mobile_url, headers=mobile_headers, timeout=15)
        req.raise_for_status()
        html = req.text
        
        # 응답이 너무 짧으면 데스크톱 버전 시도
        if len(html) < 1000:
            time.sleep(2)  # 추가 대기 시간
            base_url = "http://gall.dcinside.com/board/lists/"
            _url = f"{base_url}?id={gall_name}&page={page}"
            req = session.get(url=_url, headers=_headers, timeout=15)
            req.raise_for_status()
            html = req.text
            
            if len(html) < 1000:
                print(f"페이지 {page} 응답이 너무 짧습니다 ({len(html)}바이트). "
                      "차단되었을 가능성이 있습니다.")
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
                    # 상대 경로를 절대 경로로 변환
                    if href.startswith('/'):
                        if '/board/' in href and href.count('/') >= 3:
                            # 모바일 형식: /board/gall_name/post_num
                            parts = href.split('/')
                            if len(parts) >= 4:
                                post_num = parts[3]
                            else:
                                post_num = _extract_post_num(href)
                        else:
                            href = 'http://gall.dcinside.com' + href
                            post_num = _extract_post_num(href)
                    else:
                        post_num = _extract_post_num(href)

                    if title and post_num:
                        temp.append({
                            'title': title,
                            'post_num': post_num
                        })
            except (AttributeError, IndexError, TypeError):
                continue

        if temp:
            return_data[page] = temp
    except requests.RequestException as e:
        print(f"페이지 {page} 요청 실패: {e}")
        return_data[page] = []
    except Exception as e:
        print(f"페이지 {page} 파싱 오류: {e}")
        return_data[page] = []


def main(gall_name, start_page=1, end_page=1):
    """
    갤러리의 글 목록을 가져옵니다.

    Args:
        gall_name: 갤러리 영문 이름 (예: 'dcbest', 'programming')
        start_page: 시작 페이지 (기본값: 1)
        end_page: 마지막 페이지 (기본값: 1)

    Returns:
        dict: {페이지번호: [{'title': '제목', 'post_num': '글번호'}, ...]}

    Example:
        data = dcapi.read.title("dcbest", 1, 3)
        # {1: [{'title': '제목1', 'post_num': '1234567'}, ...],
        #  2: [...], 3: [...]}

        # 첫 페이지 첫 번째 글의 제목과 글 번호
        first_post = data[1][0]
        print(first_post['title'])  # 제목
        print(first_post['post_num'])  # 글 번호

        # 글 번호로 상세 정보 가져오기
        post_data = dcapi.read.post("dcbest", first_post['post_num'])
    """
    start = start_page
    end = end_page + 1
    return_data = {}
    for i in range(start, end):
        _req(gall_name, i, return_data)
        # 요청 간격을 두어 봇 차단 방지 (마지막 페이지 제외)
        if i < end - 1:
            time.sleep(1.5)  # 1.5초 대기
    return return_data

# 해당 갤러리 글들의 제목들을 가져옵니다.
# data = dcapi.read.title("programming")
# print(data)
# -> {1: ['첫번째글'],['두번째글'], ... }
# 가져오고싶은 페이지 구간을 적어줄수있습니다
# data = dcapi.read.title("programming",1,5) # 1페이지부터 5페이지까지 제목들을 가져오기
# print(data)
# -> {1: ['첫번째글'],['두번째글'], ... ,2 : ['첫번째글'],['두번째글'], ... }
# print(data[2]) # 다수의 페이지를 가져와 원하는 페이지들의 제목만 볼수도있습니다.
# -> {2 : ['첫번째글'],['두번째글'], ... }
# print(data[2][10]) # 원하는 페이지에 원하는 인덱스의 제목만도 가져올수있습니다.
# -> 10번째글의 제목입니다.
