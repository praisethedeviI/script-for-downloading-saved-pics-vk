import requests
import json
import os
from requests_futures import sessions

TOKEN_URL_TEMPLATE = 'https://api.vk.com/oauth/token' \
                     '?grant_type=password' \
                     '&client_id=2274003' \
                     '&client_secret=hHbZxrka2uZ6jB1inYsH' \
                     '&username={username}' \
                     '&password={password}'

PHOTOS_URL_TEMPLATE = 'https://api.vk.com/method/photos.get' \
                      '?v=5.52' \
                      '&album_id=saved' \
                      '&count=1000' \
                      '&access_token={token}' \
                      '&offset={offset}'


def main():
    username, password = get_user_info()

    json_obj = make_api_request(0, username, password)
    photo_objs = json_obj['response']['items']

    count = json_obj['response']['count']

    remain = count - 1000
    offset = 1000
    while remain > 0:
        json_obj = make_api_request(offset, username, password)
        photo_objs += json_obj['response']['items']
        remain -= 1000
        offset += 1000

    make_dir()
    download_images(photo_objs)


def get_user_info():
    username = input('Print your username, email or phone number:\n')
    password = input('Print your password:\n')
    return username, password


def make_dir():
    path = 'images/'
    try:
        os.mkdir(path)
    except OSError:
        pass


def download_images(photo_objs):
    photo_urls = []
    for i in photo_objs:
        max_size = 0
        for j in i:
            if 'photo' in j:
                a = int(j.split('_')[1])
                if a > max_size != 0:
                    photo_urls.pop()
                    photo_urls.append(i[j])
                elif a > max_size:
                    max_size = a
                    photo_urls.append(i[j])

    session = sessions.FuturesSession()

    futures = [
        session.get(photo_urls[i])
        for i in range(len(photo_urls))
    ]
    print('You have ' + str(len(futures)) + ' saved images')

    for i in range(len(futures)):
        pos = i + 1
        data = futures[i].result().content
        with open('images/' + str(pos) + '.jpg', 'wb') as handler:
            handler.write(data)
        print(
            'downloaded '
            + str(round(float(pos / len(futures) * 100), 2))
            + '% of '
            + str(len(futures))
            + ' pictures'
        )


def make_api_request(offset=0, username='', password=''):
    session = requests.Session()
    TOKEN_URL = TOKEN_URL_TEMPLATE.format(username=username, password=password)
    request = session.get(TOKEN_URL)
    if not request.ok:
        request_result = json.loads(request.text)
        if request_result['error'] == 'need_captcha':
            captcha_key = input('Write text from this captcha: '
                                + request_result['captcha_img'] + '\n')
            captcha_sid = request_result['captcha_sid']
            request = session.get(
                TOKEN_URL
                + '&captcha_sid=' + captcha_sid
                + '&captcha_key=' + captcha_key
            )
        if not request.ok:
            try:
                print(json.loads(request.text)['error_description'])
            except KeyError:
                print(request.text)
            exit(request.status_code)

    token = json.loads(request.text)['access_token']

    request = session.get(
        PHOTOS_URL_TEMPLATE.format(token=token, offset=offset)
    )
    if not request.ok:
        try:
            print(json.loads(request.text)['error_description'])
        except KeyError:
            print(request.text)
        exit(request.status_code)
    json_obj = json.loads(request.text)
    return json_obj


if __name__ == '__main__':
    main()
