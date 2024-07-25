from django.shortcuts import render
import json
import requests
try:
    import pandas as pd
except ImportError as e:
    print("Pandas could not be imported:", e)

# Create your views here.

def home(request):
    return render(request, 'app/home.html')

def search_result(request):
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
            results.append({'restaurant_id': index, 'id': id, 'Name': name, 'Address': address, 'Category': category})

        # 검색 결과를 context에 추가
        context['results'] = results
        
        # 검색 결과를 세션에 저장
        request.session['search_results'] = results

    return render(request, 'app/search_result.html', context)

def search_detail(request, id):
    # 세션에서 검색 결과 가져오기
    results = request.session.get('search_results', [])
    
    # id를 문자열로 변환 후 검색
    result = next((item for item in results if item['id'] == str(id)), None)

    context = {'result': result}
    return render(request, 'app/search_detail.html', context)
