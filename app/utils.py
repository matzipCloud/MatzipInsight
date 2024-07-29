import csv
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from konlpy.tag import Okt
import PIL

def save_reviews_to_csv(reviews, id):
    #파일 이름과 경로 지정
    filename = f'reviews_{id}.csv'
    filepath = os.path.join('data/', filename)

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Nickname', 'Content', 'Date', 'Revisit'])#헤더 작성
        for review in reviews:
            writer.writerow([review['nickname'], review['content'], review['date'], review['revisit']])

    return filepath

def make_cloud(file, id):

    #파일 불러오기
    df = pd.read_csv(file)
    print("파일 읽기 완료")

    #데이터 전처리
    df['Content'] = df['Content'].str.replace('[^가-힇]', '', regex = True)
    clean_df = df.dropna()
    print("데이터 전처리 완료")
    #형태소 분석기 로드
    okt = Okt()

    #형태소 분석 적용
    tokens = clean_df['Content'].map(lambda s: okt.nouns(s))
    #개별 단어 열로 정렬
    tokens = tokens.explode()
    #2글자 이상 단어만 표시
    df_word = pd.DataFrame({'word':tokens})
    df_word['count'] = df_word['word'].str.len()
    df_word = df_word.query('count >= 2')

    #단어별로 groupby
    df_word = df_word.groupby('word', as_index=False).count().sort_values('count', ascending=False)
    #무의미한 상위 3개 단어 제거
    df_word = df_word.iloc[3:, :]

    #dataframe을 dict으로 변환
    dic_word = df_word.set_index('word').to_dict()['count']
    print("형태소 분석 완료")
    #구름 모양 설정
    icon = PIL.Image.open('static/images/cloud.png')
    img = PIL.Image.new('RGB', icon.size, (255,255,255))
    img.paste(icon, icon)
    img = np.array(img)

    #워드 클라우드 생성
    wc = WordCloud(random_state = 123, font_path='C:/Windows/Fonts/gulim.ttc', width=200, height=160,
                   background_color='white', mask=img, colormap='Paired')

    img_wc = wc.generate_from_frequencies(dic_word)

    file_name = f'cloud_{id}.png'
    file_path = os.path.join('static/images', file_name)
    # plt.figure(figsize = (10,10)) #크기 지정
    plt.axis('off') #축없애기
    plt.imshow(img_wc) #결과 보여주기
    plt.savefig(file_path) #파일저장
    print("구름생성완료")
    return (file_path)