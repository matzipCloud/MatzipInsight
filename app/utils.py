import csv
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from konlpy.tag import Okt
import PIL
from openai import OpenAI
from dotenv import load_dotenv
import matplotlib
matplotlib.use('Agg')

#csv 파일 저장
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

#워드클라우드 생성 함수
def create_wordcloud(df, filename):
    #데이터 전처리
    text_series = df['content'].str.replace('[^가-힇]', '',regex=True)
    clean_text = ' '.join(text_series.dropna())

    okt = Okt()

    tokens = okt.nouns(clean_text)

    tokens = [word for word in tokens if len(word)>1]
    #구름 모양 설정
    icon = PIL.Image.open('static/images/cloud.png')
    img = PIL.Image.new('RGB', icon.size, (255,255,255))
    img.paste(icon, icon)
    img = np.array(img)

    #단어 빈도수 계산
    word_freq = pd.Series(tokens).value_counts().to_dict()
    # 워드 클라우드 생성
    wc = WordCloud(
        font_path='C:/Windows/Fonts/gulim.ttc',  # 한국어 폰트 경로
        width=300,
        height=300,
        background_color='white',
        mask=img,
        colormap='Paired'
    ).generate_from_frequencies(word_freq)

    # 워드 클라우드 시각화 및 저장
    plt.figure(figsize=(5, 5))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    file_path = os.path.join('static/images/', filename)
    plt.savefig(file_path, format='png')
    plt.close()
    icon.close()
    print(f"워드 클라우드 생성 완료: {file_path}")

    return filename

def analyze_sentiment(data):

    # 감성 분석 함수
    def get_sentiment(text):
        # OpenAI API 키 설정
        load_dotenv()
        client = OpenAI(api_key= os.environ.get("OPENAI_API_KEY"))
        prompt = f"Sentence: \"{text}\". Please analyze the sentiment and tell me if it is 'positive' or 'negative'."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that performs sentiment analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10  # 결과가 간단하므로 적은 토큰 수를 설정
        )
        result = response.choices[0].message.content.strip().lower()
        if "positive" in result:
            return 1
        elif "negative" in result:
            return -1
        else: return 1
    print("데이터 불러오기 중")
    #파일 불러오기
    df = pd.DataFrame(data)
    print("감성분석 중")
    # 각 행에 대해 감성 분석 수행
    df['sentiment'] = df['content'].apply(get_sentiment)

    #긍정, 부정 문장 분리
    positive_texts = df[df['sentiment']== 1]['content'].reset_index(drop=True)
    negative_texts = df[df['sentiment']== -1]['content'].reset_index(drop=True)
    print("감정 분류 완료")

    return positive_texts, negative_texts

def sentiment_cloud(data):
    positive_text, negative_text = analyze_sentiment(data)

    positive_df = pd.DataFrame(positive_text)
    negative_df = pd.DataFrame(negative_text)

    p_cloud = create_wordcloud(positive_df, "positive_cloud.png")

    n_cloud = None
    if not negative_df.empty:
        n_cloud = create_wordcloud(negative_df, "negative_cloud.png")

    return positive_df,negative_df ,p_cloud, n_cloud