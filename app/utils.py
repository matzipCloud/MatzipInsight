import csv
import os

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