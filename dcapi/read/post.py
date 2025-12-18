# -*- coding:utf-8 -*-
import requests
from bs4 import BeautifulSoup
import re

# 갤러리 영문이름과 원하는 읽고자 하는 글의 번호를 받습니다.
# gall_name : 갤러리 영문이름
# post_num : 포스트 번호

def pars_title(soup): # 제목 
    # 일반 갤러리 형식
    title = soup.find_all("span",{"class":"title_subject"})
    if not title:
        # 마이너 갤러리 형식 시도 (정확한 클래스명)
        title = soup.find_all("span", class_=lambda x: x and 'title_subject' in str(x))
    if not title:
        # 마이너 갤러리 다른 형식 시도
        title = soup.find_all("span", class_=lambda x: x and 'title' in str(x).lower() and 'subject' in str(x).lower())
    if not title:
        # h3 태그에서 제목 찾기
        title = soup.find_all("h3", class_=lambda x: x and 'title' in str(x).lower())
    if not title:
        # div 태그에서 제목 찾기
        title = soup.find_all("div", class_=lambda x: x and 'title' in str(x).lower())
    if not title:
        # id로 찾기
        title = soup.find_all(id=re.compile(r'title', re.I))
    if not title:
        # data 속성으로 찾기
        title = soup.find_all(attrs={"data-title": True})
    if not title:
        # 마지막 시도: 제목이 포함된 모든 요소 (너무 많은 결과를 피하기 위해 제한)
        title = soup.find_all(["span", "h3", "div", "p"], string=lambda text: text and len(text.strip()) > 5)
        # 가장 긴 텍스트를 제목으로 선택 (일반적으로 제목이 가장 길 수 있음)
        if title:
            title = [max(title, key=lambda x: len(x.getText().strip()))]
    
    if title:
        return title[0].getText().strip()
    else:
        # 디버깅을 위해 HTML 일부 출력
        print(f"[DEBUG] 제목을 찾을 수 없습니다. HTML 샘플:")
        print(soup.prettify()[:1000])  # 처음 1000자만 출력
        raise IndexError("제목을 찾을 수 없습니다.")

def pars_writer(soup): # 글쓴이 
    writer = soup.find_all("span",{"class" : "nickname"})
    return writer[0].get('title')

def pars_time(soup): # 작성시간
    time = soup.find_all("span",{"class" : "gall_date"})
    return time[0].get('title')

def pars_ip(soup): # IP 
    ip = soup.find_all("span",{"class" : "ip"})
    return ip[0].getText()

def pars_view(soup): # 조회수
    view = soup.find_all("span",{"class" : "gall_count"})
    view = view[0].getText()
    view = view.split("조회 ")
    return view[1]

def pars_comment(soup): # 댓글수
    comment = soup.find_all("span",{"class" : "gall_comment"})
    comment = comment[0].getText()
    comment = comment.split("댓글 ")
    return comment[1]

def pars_up(soup,post_num): # 추천수
    up = soup.find_all("p",{"id" : "recommend_view_up_"+str(post_num)})
    return up[0].getText()

def pars_down(soup,post_num): # 비추천수
    down = soup.find_all("p",{"id" : "recommend_view_down_"+str(post_num)})
    return down[0].getText()

def pars_gonic_up(soup,post_num): # 고닉 추천수
    gonic_up = soup.find_all("span",{"id" : "recommend_view_up_fix_"+str(post_num)})
    return gonic_up[0].getText()

def pars_content(soup): # 내용 
    # 여러 가능한 선택자 시도
    content = soup.find_all("div",{"style" : "overflow:hidden;"})
    if not content:
        # 대체 선택자 시도
        content = soup.find_all("div", class_=lambda x: x and 'writing_view_box' in str(x))
    if not content:
        content = soup.find_all("div", id=re.compile(r'viewContent'))
    if not content:
        # 가장 일반적인 내용 영역 찾기
        content = soup.find_all("div", class_=lambda x: x and 'view_content' in str(x).lower())
    
    if content:
        return content[0].getText()
    else:
        return "내용을 찾을 수 없습니다."

def pars_images(soup): # 이미지 URL 추출
    """글 내용에서 이미지 URL을 추출합니다."""
    images = []
    
    # 여러 가능한 선택자로 내용 영역 찾기
    content_divs = soup.find_all("div",{"style" : "overflow:hidden;"})
    if not content_divs:
        content_divs = soup.find_all("div", class_=lambda x: x and 'writing_view_box' in str(x))
    if not content_divs:
        content_divs = soup.find_all("div", id=re.compile(r'viewContent'))
    if not content_divs:
        content_divs = soup.find_all("div", class_=lambda x: x and 'view_content' in str(x).lower())
    
    if not content_divs:
        return images
    
    # 내용 영역에서 이미지 찾기
    content_div = content_divs[0]
    
    # img 태그 찾기
    img_tags = content_div.find_all('img')
    for img in img_tags:
        src = img.get('src', '') or img.get('data-src', '') or img.get('data-original', '')
        if src:
            # 상대 경로를 절대 경로로 변환
            if src.startswith('//'):
                src = 'http:' + src
            elif src.startswith('/'):
                src = 'http://gall.dcinside.com' + src
            elif not src.startswith('http'):
                continue
            
            # 디시인사이드 이미지 서버 URL인지 확인
            # 로딩 이미지나 아이콘은 제외
            if ('dcinside.com' in src or 'image.dcinside.com' in src or 'img.dcinside.com' in src):
                # 로딩 이미지, 아이콘, 배너 등 제외
                if 'loading' not in src.lower() and 'icon' not in src.lower() and 'banner' not in src.lower():
                    if src not in images:  # 중복 제거
                        images.append(src)
    
    # background-image 스타일에서 이미지 URL 추출
    style_tags = content_div.find_all(style=re.compile(r'background-image'))
    for tag in style_tags:
        style = tag.get('style', '')
        match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
        if match:
            img_url = match.group(1)
            if img_url.startswith('//'):
                img_url = 'http:' + img_url
            elif img_url.startswith('/'):
                img_url = 'http://gall.dcinside.com' + img_url
            if 'dcinside.com' in img_url or 'image.dcinside.com' in img_url:
                # 로딩 이미지, 아이콘, 배너 등 제외
                if 'loading' not in img_url.lower() and 'icon' not in img_url.lower() and 'banner' not in img_url.lower():
                    if img_url not in images:  # 중복 제거
                        images.append(img_url)
    
    return images

def pars(req,data, html=None): 
    # html이 제공되지 않으면 req.text 사용
    if html is None:
        html = req.text
    soup = BeautifulSoup(html, 'lxml')
    data["title"] = pars_title(soup)
    data["writer"] = pars_writer(soup)
    data["time"] = pars_time(soup)
    data["ip"] = pars_ip(soup)
    data["view_num"] = pars_view(soup)
    data["comment_num"] = pars_comment(soup)
    data["up"] = pars_up(soup,data["post_num"])
    data["down"] = pars_down(soup,data["post_num"])
    data["gonic_up"] = pars_gonic_up(soup,data["post_num"])
    data["content"] = pars_content(soup)
    data["images"] = pars_images(soup)  # 이미지 URL 목록 추가

def _req(gall_name,post_num,data, is_minor_gallery=False):
    _headers = {
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
        "Referer": "https://gall.dcinside.com/",
    }
    # 마이너 갤러리인 경우 mgallery 경로 사용
    # https 사용 (보안 및 일관성)
    if is_minor_gallery:
        _url = "https://gall.dcinside.com/mgallery/board/view/?id="+gall_name+"&no="+str(post_num)+"&page=1"
    else:
        _url = "https://gall.dcinside.com/board/view/?id="+gall_name+"&no="+str(post_num)+"&page=1"
    req = requests.get(url=_url, headers=_headers, allow_redirects=True)
    
    # 응답 상태 확인
    if req.status_code != 200:
        raise Exception(f"HTTP {req.status_code} 오류: {_url}")
    
    # JavaScript 리다이렉트 처리 (location.replace가 있는 경우)
    html = req.text
    if '<script' in html and 'location.replace' in html:
        # location.replace URL 추출
        import re
        # 여러 패턴 시도: location.replace("url"), location.replace('url'), location.replace(url)
        match = re.search(r'location\.replace\(["\']([^"\']+)["\']\)', html)
        if not match:
            match = re.search(r'location\.replace\(([^)]+)\)', html)
        if match:
            redirect_url = match.group(1).strip('"\'').strip()
            # 상대 경로를 절대 경로로 변환
            if redirect_url.startswith('/'):
                redirect_url = 'https://gall.dcinside.com' + redirect_url
            elif not redirect_url.startswith('http'):
                redirect_url = 'https://gall.dcinside.com/' + redirect_url
            
            # 리다이렉트 URL에 page 파라미터가 없으면 추가
            if 'page=' not in redirect_url:
                if '?' in redirect_url:
                    redirect_url += '&page=1'
                else:
                    redirect_url += '?page=1'
            
            # 리다이렉트 URL로 다시 요청
            req = requests.get(url=redirect_url, headers=_headers, allow_redirects=True)
            if req.status_code != 200:
                raise Exception(f"HTTP {req.status_code} 오류 (리다이렉트 후): {redirect_url}")
    
    # 최종 HTML로 파싱
    pars(req, data)



def main(gall_name,post_num, is_minor_gallery=False):
    data = { }
    data["post_num"] = post_num
    # 일반 갤러리로 먼저 시도
    try:
        _req(gall_name,post_num,data, is_minor_gallery=False)
    except (IndexError, AttributeError, KeyError):
        # 실패 시 마이너 갤러리로 재시도
        if not is_minor_gallery:
            try:
                _req(gall_name,post_num,data, is_minor_gallery=True)
            except Exception:
                # 마이너 갤러리로도 실패하면 원래 예외 재발생
                _req(gall_name,post_num,data, is_minor_gallery=False)
        else:
            raise

    return data

# 게시글의 고유번호를 이용해 게시글의 정보를 가져옵니다
#data = dcapi.read.post("programming","930329")
#print(data)
# -> {'post_num': '930329', 'title': '제목입니다', 'writer': '닉네임', 'time': '2018-11-16 21:28:46', 'ip': '(218.153)', 'view_num': '44', 'comment_num': '0', 'up': '1', 'down': '2', 'gonic_up': '0', 'content': '내용이고요 '}
#print(data['post_num'],data['title'],data['content']) # 게시글의 원하는 정보만 사용할수도 있습니다.
# -> 930329 제목입니다 내용이고요