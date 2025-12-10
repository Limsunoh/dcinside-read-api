﻿# dcinside-python3api

##### dcinside python3 전용 비공식 API 입니다. (글 읽기 전용)

## 설치

### Git 저장소에서 설치 (권장)

```bash
pip install git+https://github.com/YOUR_USERNAME/dcinside-python3-api.git
```

또는 개발 모드로 설치:
```bash
git clone https://github.com/YOUR_USERNAME/dcinside-python3-api.git
cd dcinside-python3-api
pip install -e .
```

### 로컬에서 설치

```bash
cd dcinside-python3-api
pip install -e .
```

### 의존성 패키지

다음 패키지들이 필요합니다 (설치 시 자동으로 설치됨):
- requests
- beautifulsoup4
- lxml
- selenium

## API 기능

### dcapi.read.title(gall_name, start_page, end_page)

갤러리의 글 목록을 가져옵니다. **제목과 글 번호를 함께 반환**합니다.

```python
# 1페이지 글 목록 가져오기
data = dcapi.read.title("dcbest", 1, 1)
print(data)
# -> {1: [{'title': '첫번째글제목', 'post_num': '1234567'}, {'title': '두번째글제목', 'post_num': '1234568'}, ...]}

# 여러 페이지 가져오기 (1페이지부터 3페이지까지)
data = dcapi.read.title("dcbest", 1, 3)
print(data)
# -> {1: [...], 2: [...], 3: [...]}

# 첫 페이지 첫 번째 글의 정보
first_post = data[1][0]
print(first_post['title'])      # 제목
print(first_post['post_num'])    # 글 번호
```

**반환 형식:**
- `{페이지번호: [{'title': '제목', 'post_num': '글번호'}, ...]}`

**주의:** 디시인사이드의 봇 차단으로 인해 일반 버전은 차단될 수 있습니다. Selenium 버전을 사용하는 것을 권장합니다.

### dcapi.read.title_selenium (Selenium 버전)

Selenium을 사용하여 봇 차단을 우회하는 버전입니다.

```python
from dcapi.read.title_selenium import main as selenium_title

# 글 목록 가져오기
posts = selenium_title("dcbest", 1, 3, headless=True)
# headless=True: 브라우저 창을 띄우지 않음
# headless=False: 브라우저 창을 띄움 (디버깅용)

# 반환 형식은 일반 버전과 동일
first_post = posts[1][0]
print(first_post['title'])
print(first_post['post_num'])
```

**필요한 것:**
- Selenium 설치: `pip install selenium`
- ChromeDriver (자동으로 다운로드되거나 수동 설치 필요)

### dcapi.read.post(gall_name, post_num)

게시글의 고유번호를 이용해 게시글의 상세 정보를 가져옵니다.

```python
data = dcapi.read.post("dcbest", "1234567")
print(data)
# -> {
#   'post_num': '1234567',
#   'title': '제목입니다',
#   'writer': '닉네임',
#   'time': '2021-11-06 10:00:01',
#   'ip': '(125.244)',
#   'view_num': '37559',
#   'comment_num': '119',
#   'up': '266',
#   'down': '31',
#   'gonic_up': '88',
#   'content': '내용입니다',
#   'images': ['https://...', 'https://...']  # 이미지 URL 목록
# }

# 원하는 정보만 사용
print(data['title'])      # 제목
print(data['content'])    # 내용
print(data['images'])     # 이미지 URL 목록
```

**반환 데이터:**
- `post_num`: 글 번호
- `title`: 제목
- `writer`: 작성자
- `time`: 작성시간
- `ip`: IP 주소
- `view_num`: 조회수
- `comment_num`: 댓글수
- `up`: 추천수
- `down`: 비추천수
- `gonic_up`: 고닉 추천수
- `content`: 글 내용
- `images`: 이미지 URL 목록 (자동 추출)

### dcapi.read.reply(gall_name, post_num)

해당 글의 댓글들을 가져옵니다.

```python
data = dcapi.read.reply("dcbest", "1234567")
print(data)
# -> {
#   0: ['작성자(IP)', '댓글 내용'],
#   1: ['작성자(IP)', '댓글 내용'],
#   ...
# }

# 첫 번째 댓글
print(data[0])           # ['작성자', '내용']
print(data[0][0])        # 작성자
print(data[0][1])        # 댓글 내용
```

## 실제 사용 예제

### save_dcbest_posts.py

dcbest 갤러리에서 글을 가져와서 파일로 저장하는 스크립트입니다.

```bash
python save_dcbest_posts.py
```

**기능:**
1. 글 목록 가져오기 (Selenium 사용)
2. 각 글의 상세 정보 수집
3. 썸네일 이미지 다운로드 (각 글당 1개)
4. JSON, 텍스트, CSV 파일로 저장

**저장되는 파일:**
- `dcbest_posts_날짜시간.json`: 구조화된 데이터
- `dcbest_posts_날짜시간.txt`: 읽기 쉬운 텍스트 형식
- `dcbest_posts_날짜시간.csv`: 엑셀에서 열 수 있는 형식
- `dcbest_thumbnails_날짜시간/`: 썸네일 이미지 폴더

## 전체 사용 예제

```python
import dcapi
from dcapi.read.title_selenium import main as selenium_title

# 1. 글 목록 가져오기 (Selenium 사용 권장)
posts = selenium_title("dcbest", 1, 1, headless=True)

# 2. 첫 번째 글의 상세 정보
if posts and 1 in posts and posts[1]:
    first_post = posts[1][0]
    post_num = first_post['post_num']
    
    # 3. 상세 정보 가져오기
    detail = dcapi.read.post("dcbest", post_num)
    print(f"제목: {detail['title']}")
    print(f"내용: {detail['content']}")
    print(f"이미지: {len(detail['images'])}개")
    
    # 4. 댓글 가져오기
    replies = dcapi.read.reply("dcbest", post_num)
    print(f"댓글: {len(replies)}개")
```

## 주의사항

1. **봇 차단**: 디시인사이드가 봇 요청을 차단할 수 있습니다. Selenium 버전을 사용하는 것을 권장합니다.
2. **요청 간격**: 너무 빠른 요청은 차단될 수 있으므로 적절한 간격을 두세요.
3. **이미지 다운로드**: 이미지 다운로드 시 Referer 헤더가 필요할 수 있습니다.

## 라이선스

비공식 API입니다. 사용 시 주의하세요.
