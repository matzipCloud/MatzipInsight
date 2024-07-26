import csv
import os

def save_reviews_to_csv(reviews, id):
    # 파일 이름과 경로 지정
    filename = f'reviews_{id}.csv'
    dirpath = 'data'
    filepath = os.path.join(dirpath, filename)

    # 디렉토리가 존재하지 않으면 생성
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Nickname', 'Content', 'Date', 'Revisit'])  # 헤더 작성
        for review in reviews:
            writer.writerow([review['nickname'], review['content'], review['date'], review['revisit']])

    return filepath
