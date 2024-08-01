import csv
import os
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from wordcloud import WordCloud
from konlpy.tag import Okt
import PIL
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# NLTK VADER 다운로드
nltk.download('vader_lexicon')

def save_reviews_to_csv(reviews, id):
    # 파일 이름과 경로 지정
    filename = f'reviews_{id}.csv'
    filepath = os.path.join('data/', filename)

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Nickname', 'Content', 'Date', 'Revisit'])  # 헤더 작성
        for review in reviews:
            writer.writerow([review['nickname'], review['content'], review['date'], review['revisit']])

    print(filepath)
    return filepath

# JSON 파일 로드하는 함수
def load_sentiment_lexicon(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        lexicon = json.load(file)
    return lexicon

def analyze_sentiment(text, lexicon):
    okt = Okt()
    words = okt.pos(text)  # 형태소 분석을 통해 단어와 품사 추출
    sentiment_score = 0
    
    # 명사, 형용사, 동사만 필터링
    meaningful_words = [word for word, pos in words if pos in ['Noun', 'Adjective', 'Verb']]
    
    for word in meaningful_words:
        # lexicon에서 'word_root'가 key로 되어 있으므로 'word_root'를 기준으로 감정 점수 합산
        for item in lexicon:
            if word == item['word_root']:
                sentiment_score += int(item['polarity'])
                break
    
    # 디버깅 메시지 추가
    #print(f"Text: {text}, Words: {meaningful_words}, Sentiment Score: {sentiment_score}")
    
    # 감정 점수를 기반으로 긍정/부정 판단
    return 1 if sentiment_score > 0 else 0

def sentiment_analysis(df, lexicon):
    # 열 이름을 소문자로 변환하여 일관성 유지
    df.columns = df.columns.str.lower()
    
    # 감정 분석
    df['sentiment'] = df['content'].apply(lambda text: analyze_sentiment(text, lexicon))
    
    # 긍정 및 부정 리뷰 분리
    positive_reviews = df[df['sentiment'] == 1]
    negative_reviews = df[df['sentiment'] == 0]

    return positive_reviews, negative_reviews

def make_cloud(file, id, sentiment):
    # 파일 불러오기
    df = pd.read_csv(file)
    print("파일 읽기 완료")

    # 데이터 전처리
    df['content'] = df['content'].str.replace('[^가-힇]', '', regex=True)  # 한글이 아닌 문자 제거
    clean_df = df.dropna()  # 결측값 제거
    print("데이터 전처리 완료")
    
    # 형태소 분석기 로드
    okt = Okt()
    tokens = clean_df['content'].map(lambda s: okt.nouns(s))  # 명사 추출
    tokens = tokens.explode()  # 개별 단어 열로 정렬
    
    # 2글자 이상 단어만 표시
    df_word = pd.DataFrame({'word': tokens})
    df_word['count'] = df_word['word'].str.len()  # 단어의 길이를 계산
    df_word = df_word.query('count >= 2')  # 두 글자 이상 단어 필터링
    df_word = df_word.groupby('word', as_index=False).count().sort_values('count', ascending=False)  # 단어별로 그룹화
    df_word = df_word.iloc[3:, :]  # 무의미한 상위 3개 단어 제거

    # dataframe을 dict으로 변환
    dic_word = df_word.set_index('word').to_dict()['count']
    print("형태소 분석 완료")

    # 구름 모양 설정
    icon = PIL.Image.open('static/images/cloud.png')
    img = PIL.Image.new('RGB', icon.size, (255, 255, 255))
    img.paste(icon, icon)
    img = np.array(img)

    # 워드 클라우드 생성
    wc = WordCloud(random_state=123, font_path='C:/Windows/Fonts/gulim.ttc',
                   background_color='white', mask=img, colormap='Paired')

    img_wc = wc.generate_from_frequencies(dic_word)

    file_name = f'cloud_{sentiment}.png'
    file_path = os.path.join('static/images', file_name)
    
    plt.axis('off')
    plt.imshow(img_wc)
    plt.savefig(file_path)
    plt.close()
    print("구름 생성 완료")
    return file_name

def generate_wordclouds(csv_file_path, id):
    # 리뷰 데이터를 CSV 파일에서 읽어옵니다.
    reviews_df = pd.read_csv(csv_file_path)
    print("리뷰 데이터 읽어오기")
    print(reviews_df.head())  # 전체 데이터프레임의 첫 5행 출력
    
    # 감정 분석 사전 로드
    json_filename = 'SentiWord_info.json'
    json_filepath = os.path.join('json/', json_filename)
    
    sentiment_lexicon = load_sentiment_lexicon(json_filepath)
    
    # 긍정 및 부정 리뷰로 분류합니다.
    positive_reviews, negative_reviews = sentiment_analysis(reviews_df, sentiment_lexicon)

    # 긍정 및 부정 리뷰를 CSV 파일로 저장
    positive_file = f'data/positive_reviews_{id}.csv'
    negative_file = f'data/negative_reviews_{id}.csv'
    positive_reviews.to_csv(positive_file, index=False, encoding='utf-8-sig')
    negative_reviews.to_csv(negative_file, index=False, encoding='utf-8-sig')

    # 워드 클라우드를 생성합니다.
    positive_cloud = make_cloud(positive_file, id, "positive")
    negative_cloud = make_cloud(negative_file, id, "negative")

    return positive_cloud, negative_cloud