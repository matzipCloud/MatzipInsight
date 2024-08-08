from django.shortcuts import render
from django.http import JsonResponse
from django.http import JsonResponse
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from .utils import *
import os
import time
import requests
try:
    import pandas as pd
except ImportError as e:
    print("Pandas could not be imported:", e)


# Create your views here.

def home(request):
    return render(request, 'app/home.html')


def search_result(request):
    """
    사용자로부터 검색어를 받아 네이버 지도 API를 통해 검색 결과를 가져옵니다.
    검색 결과를 세션에 저장하고, 검색 결과를 템플릿에 전달합니다.
    """
    query = request.GET.get('query')  # 사용자로부터 검색어를 가져옴
    sort = request.GET.get('sort', 'distance')  # 정렬 기준을 가져옴 (기본값은 'distance')
    context = {'query': query}

    if query:
        url = 'https://m.map.naver.com/search2/searchMore.naver'

        # 요청 헤더
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }

        # 요청 파라미터
        params = {
            'query': query,
            'sm': 'hty',
            'style': 'v5',
            'type': 'SITE_1',  # 검색 결과 타입 설정
            'displayCount': 100
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # 요청 실패 시 에러 발생
        data = response.json()
        

        # 검색 결과를 저장할 리스트 초기화
        results = []

        # 검색 결과 출력
        for item in data.get('result', {}).get('site', {}).get('list', []):
            id = item.get('id')
            name = item.get('name')
            address = item.get('address')
            category = item.get('category')
            thumUrl = item.get('thumUrl')
            latitude = item.get('y')  # API 응답에서 latitude 값을 가져옴
            longitude = item.get('x')  # API 응답에서 longitude 값을 가져옴
            distance = item.get('distance', float('inf'))  # 거리 정보 가져오기 (가정)
            reviews = item.get('reviews', 0)  # 리뷰 수 정보 가져오기 (가정)
            

            results.append({
                'id': id, 
                'Name': name, 
                'Address': address, 
                'Category': category, 
                'thumUrl': thumUrl,
                'latitude': latitude,
                'longitude': longitude,
                'distance': distance,
                'reviews': reviews
            })

        # 검색 결과를 context에 추가
        context['results'] = results
        
        # .env 파일 context에 추가
        load_dotenv()
        ncpClientId = os.environ.get('NAVER_CLIENT_ID')
        context['ncpClientId'] = ncpClientId

        # 검색 결과를 세션에 저장
        request.session['search_results'] = results

    return render(request, 'app/search_result.html', context)


def search_detail(request, id):
    # 세션에서 검색 결과 가져오기
    results = request.session.get('search_results', [])

    # id를 문자열로 변환 후 검색
    result = next((item for item in results if item['id'] == str(id)), None)

    context = {'result': result}

    # 리뷰 데이터를 저장할 리스트 초기화
    reviews = []

    try:
        # Selenium을 사용하여 리뷰 페이지 크롤링
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument('user-agent=' + user_agent)
        #위치정보 허용
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.geolocation": 1
        })
        driver = webdriver.Chrome(options=options)

        res = driver.get(f'https://m.place.naver.com/restaurant/{id}/review/visitor')
        driver.implicitly_wait(20)

        # Pagedown
        time.sleep(2)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)

        # 최대 n개의 리뷰를 가져오기 위한 루프
        while len(reviews) < 500:
            try:
                driver.find_element(By.XPATH,
                                    '//*[@id="app-root"]/div/div/div/div[6]/div[2]/div[3]/div[2]/div/a').click()
                time.sleep(0.05)
            except Exception as e:
                print('finish')
                break

            # 크롤링
            html = driver.page_source
            bs = BeautifulSoup(html, 'html.parser')
            review_elements = bs.select('li.owAeM')

            for review in review_elements:
                if len(reviews) >= 500:
                    break
                # 개별 콘텐츠 선택하여 읽어들이는 부분
                nickname = review.select_one('span.P9EZi')
                content = review.select_one('span.zPfVt')
                date = review.select_one('span.CKUdu > span.place_blind:nth-of-type(2)')
                revisit = review.select_one('span.CKUdu:nth-of-type(2)')

                # 예외 처리
                nickname = nickname.text if nickname else ''
                content = content.text if content else ''
                date = date.text if date else ''
                revisit = revisit.text if revisit else ''

                reviews.append({'nickname': nickname, 'content': content, 'date': date, 'revisit': revisit})
                time.sleep(0.05)

        # context['reviews'] = reviews[:5]
        print("크롤링 완료")

        df_reviews = pd.DataFrame(reviews)
        #재방문 바 그래프
        context['graph'] = 'images/'+revisit_bargraph(df_reviews)

        #중복제거
        df_reviews.drop_duplicates(inplace=True)
        #감성분석
        p_df, n_df, positive_img, negative_img = sentiment_cloud(df_reviews)

        #긍정 리뷰가 없을때 예외처리
        if p_df.empty:
            context['positiveness'] = []
        else:
            context['positiveness'] = p_df[:5].to_dict(orient='records')

        #부정 리뷰가 없을때 예외처리
        if p_df.empty:
            context['negativeness'] = []
        else:
            context['negativeness'] = n_df[:5].to_dict(orient='records')

        context['positive_img'] = 'images/'+positive_img
        context['negative_img'] = 'images/'+negative_img
        print("구름생성완료")

    except Exception as e:
        print(e)
    finally:
        driver.quit()

    return render(request, 'app/search_detail.html', context)


def delete_review_file(request, id):
    filenames = ['positive_cloud.png', 'negative_cloud.png', 'bargraph.png']
    filepaths = [os.path.join('static/images', filename) for filename in filenames]

    files_deleted = False
    for filepath in filepaths:
        if os.path.exists(filepath):
            os.remove(filepath)
            files_deleted = True

    if files_deleted:
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'file not found'}, status=404)