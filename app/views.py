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
        for index, item in enumerate(data.get('result', {}).get('site', {}).get('list', [])):
            id = item.get('id')
            name = item.get('name')
            address = item.get('address')
            category = item.get('category')
            thumUrl = item.get('thumUrl')
            latitude = item.get('y')  # API 응답에서 latitude 값을 가져옴
            longitude = item.get('x')  # API 응답에서 longitude 값을 가져옴
            results.append({
                'id': id, 
                'Name': name, 
                'Address': address, 
                'Category': category, 
                'thumUrl': thumUrl,
                'latitude': latitude,
                'longitude': longitude
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
    """
    선택된 식당의 상세 정보를 보여줍니다.
    리뷰를 크롤링하고, 긍정 및 부정 리뷰에 대한 워드 클라우드를 생성합니다.
    """
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
        driver = webdriver.Chrome(options=options)

        # 식당 리뷰 페이지 열기
        driver.get(f'https://m.place.naver.com/restaurant/{id}/review/visitor')
        driver.implicitly_wait(20)
        
        # 페이지를 스크롤하여 리뷰 더 불러오기
        time.sleep(5)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)

        # 최대 100개의 리뷰를 가져오기 위한 루프
        while len(reviews) < 100:
            try:
                # "더보기" 버튼 클릭
                driver.find_element(By.XPATH,
                                    '//*[@id="app-root"]/div/div/div/div[6]/div[2]/div[3]/div[2]/div/a').click()
                time.sleep(0.05)
            except Exception as e:
                print('finish')
                break

            # 페이지 소스를 가져와서 파싱
            html = driver.page_source
            bs = BeautifulSoup(html, 'html.parser')
            review_elements = bs.select('li.owAeM')

            for review in review_elements:
                if len(reviews) >= 100:
                    break
                # 개별 리뷰 내용 추출
                nickname = review.select_one('span.P9EZi')
                content = review.select_one('span.zPfVt')
                date = review.select_one('span.CKUdu > span.place_blind:nth-of-type(2)')
                revisit = review.select_one('span.CKUdu:nth-of-type(2)')

                # 리뷰 데이터 정제
                nickname = nickname.text if nickname else ''
                content = content.text if content else ''
                date = date.text if date else ''
                revisit = revisit.text if revisit else ''

                reviews.append({'nickname': nickname, 'content': content, 'date': date, 'revisit': revisit})
                time.sleep(0.05)

        context['reviews'] = reviews[:5]  # 리뷰 상위 5개만 표시

        # 리뷰 데이터를 CSV 파일로 저장
        csv_file = save_reviews_to_csv(reviews, id)
        
        # 긍정 및 부정 리뷰 워드 클라우드 생성
        cloud_positive, cloud_negative = generate_wordclouds(csv_file, id)
        
        context['cloud_positive'] = "images/" + cloud_positive
        context['cloud_negative'] = "images/" + cloud_negative

    except Exception as e:
        print(e)
    finally:
        driver.quit()  # 드라이버 종료

    return render(request, 'app/search_detail.html', context)


def delete_review_file(request, id):
    """
    리뷰 CSV 파일과 워드 클라우드 이미지를 삭제합니다.
    """
    # 파일 경로 설정
    filenames = [
        f'reviews_{id}.csv',
        f'positive_reviews_{id}.csv',
        f'negative_reviews_{id}.csv',
        f'cloud_{id}.png',
        'cloud_positive.png',  # 추가된 파일
        'cloud_negative.png'   # 추가된 파일
    ]
    
    filepaths = [os.path.join('data/', filename) for filename in filenames[:3]] + [os.path.join('static/images', filename) for filename in filenames[3:]]

    deleted_files = []
    not_found_files = []

    for filepath in filepaths:
        if os.path.exists(filepath):
            os.remove(filepath)
            deleted_files.append(filepath)
        else:
            not_found_files.append(filepath)

    # 응답 생성
    if deleted_files:
        response_data = {
            'status': 'success',
            'deleted_files': deleted_files,
            'not_found_files': not_found_files
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({'status': 'no files found'}, status=404)