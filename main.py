#!/bin/python

import discum
import argparse
import cv2
import numpy as np
import pytesseract
import urllib3
import re

ap = argparse.ArgumentParser()
ap.add_argument("-u", "--user", type=str, help="Shadow-Illusion User", required=True)
ap.add_argument("-p", "--password", type=str, help="Shadow-Illusion Password", required=True)
ap.add_argument("-t", "--token", type=str, help="Discord Token")
ap.add_argument("-c", "--channel", type=str, help="Discord Channel to Watch. Defaults to any if not set")
ap.add_argument("-g", "--guild", type=str, help="Discord Server ID", default='818487757520371774')
ap.add_argument("-l", "--log", type=bool, help="Whether to log bot actions", default=False)
args = vars(ap.parse_args())

token = args["token"]

shadowUser = args["user"]
shadowPass = args["password"]
guildId = args["guild"]

channelId = args['channel']
log = args["log"]

http = urllib3.PoolManager()
bot = discum.Client(token=token, log=log)

def url_to_image(url):
    resp = http.request('GET', url)
    image = np.asarray(bytearray(resp.data), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image

def read_image_text(url):
    resp = http.request('GET', url)
    image = np.asarray(bytearray(resp.data), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    text = pytesseract.image_to_string(image, config=r'--oem 3 --psm 6')
    return text

def get_shadow_token():
    body = '{account_login: %s, account_password: %s}' % (shadowUser, shadowPass)
    resp = http.request('POST', 'https://shadow-illusion.com/?account/manage', headers={'Content-Type': 'application/json'}, body=body)
    cookies = resp.info().get('Set-Cookie')
    session = re.findall("(PHPSESSID=[a-zA-Z0-9]+\\b)", cookies)
    return session[0]

def insert_code(code):
    body = '{code: %s}' % (code)
    session = get_shadow_token()
    http.request('POST', 'https://shadow-illusion.com/?sms_pay', headers={'Content-Type': 'application/json', 'Cookie': session}, body=body)

@bot.gateway.command
def parser(resp):
    if resp.event.ready_supplemental:
        user = bot.gateway.session.user
        print("Logged in as {}#{}".format(user['username'], user['discriminator']))
    if resp.event.message:
        m = resp.parsed.auto()
        guildID = m['guild_id'] if 'guild_id' in m else None
        correctChannel = True if not channelId else m['channel_id'] == channelId
        content = m['content']
        attachments = m['attachments']

        if guildID == guildId and correctChannel:
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
            for url in urls:
                text = read_image_text(url)
                print(text)
                codes = re.findall("\\b([a-z0-9]{8})\\b", text)
                for code in codes:
                    insert_code(code)
            for attachment in attachments:
                text = read_image_text(attachment['url'])
                print(text)
                codes = re.findall("\\b([a-z0-9]{8})\\b", text)
                for code in codes:
                    insert_code(code)

bot.gateway.run(auto_reconnect=True)
