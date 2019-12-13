import os

import requests
import slackweb
import json
from flask import Flask, request, abort, Response
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, ImageMessage, StickerMessage, TextSendMessage

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credential = {
  "project_id": "brave-octane-261912",
  "private_key_id": "7db531f7db27f7a248bb4684bb7870d02bb90a79",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC56921qyeUbBnH\n6TuKqCxgAGdGBM9MTlEgosQRiFrxR5JHUM05PsTU2EzRRCOOKIWSL7MWdX63fYlS\nV74fXWA5IGiQhQ0Va50nu4ptBT8qFXBuCv0NxicKinilOTVk7Gp6lNkMYsYxCCr8\n0ajKnT6qsNR7qDbA2r6jVZgGk5fUkmnpFGZ71A18wsGdfUIKNSsA49jl9Y652evG\nE4lDgqkeIH5X7+ao7ROabOMLIhICac45kA8zaX6FzrbTSA2TcwZ42dpNWIu7SRJf\n6htHWitkH97NYCDJ3D/d4EknLmMDR4lWgfxX3hVAgzh9w4vT7y/8m1ceEQLwBNoX\n9vyOIi8nAgMBAAECggEAWS18g+YbrwKG/y+tIp314vpujtRBxn0ORtQrrak0zeSh\nkll8hofIC7vQZNQFJevj3bHJee1ToZmyY2+4vvyf6ebUoPVgyDR9BhDbnd1VZc8w\nxWe554BzO4gdxEqDhOwtSqzYyysZm20qiWfbSYxRAbidws51rN1/cYLdz9G9kvTy\nA4+f2CXsy00IFQmryT2J9U9BMlyMR3qyTcg0aiVdrWwvm8zmBy4nAa9RpJ6xe+nh\nHkk/5O/u+feKH7hodpU1tVwHFylSGsMDSb7SJFRBcH2h03js9XJvC+ETRIHBvROI\n/iHQfiQ+m7QQ4u6/1Vj6/71LKp5l8kE0tOBbJvm7yQKBgQDmceaFwuUDnEFcz8HT\nkh9XKIKIkIzVNsZJLO6qR2QRQ2siv78fQ6eX295PtcJ3qOQ+kl+DZW6wxV9ckESl\nR3m/uQvq2uw+LCMwBoCVxNlKX8/3EyzrHYMUqAgCvfNNMVfCpriaXWiWcFJ9xtlj\nlZvyJCmd1dzn7hXru8jfcWH97QKBgQDOifx1QCvfhwXdm6hzJPNpBj6E+FX22+Sf\ncVMszdT9td32ZEk6Wkiy2s4aQIwK8NaoH7LL4N/r+V9Ekp9mcr2nP51+DzhgQbMY\n2XbYfmdkC1kII4aS+T0gLlwUwO5aOrAdlWcAK/vFrlCZbkyql5c7M3cIxjdG58hK\nBItX9OVe4wKBgHWs0CSaA0w2rIHybW3Wfj6Jpy6JcgEmuVaApVc6oXTXUowqEjSq\n3ZgEZJ+blzR3gCYbpL56O231O98OpJ8pwpgOrHE/XcfZzhYmG99e5/68snvexN9C\n8L7Jl12fFfDjM4doj3f0HwZDUTx9IGFj8oBRyxaYMPgWcgcwm0DOq1V5AoGAQb5A\ngx4LGRrErjbHFufTJ0Iakn7t9icmje4nuKJIQv4qCiz/9jgY3f2yDz8ulKj22wtE\nAYuyG04EmjJF1Pl/Dwa73g2AN3uSQ72tC9qolHrcOy/7vTrizySSoPSMqmH1/2S4\nJaDagqEq/LvUYZThSbHnGP7nR4WuBomNxVCp1lsCgYEAqFuFdGh9Bu32zrcDfABs\nSA5spOXPpWYJi9n1nNB/zEaENysLclQ3S5x2pAqumMZISMDiWxbaykQYY6oS4LX+\noX7VP2phl5AgndILodZtCiEq5cImqa4trSSzA3hRt72FWCCMEjb9ezJxbYlgC9tl\nvfwJ8Es8heZdDNApP+lD7OE=\n-----END PRIVATE KEY-----\n",
  "client_email": "laimo-410@brave-octane-261912.iam.gserviceaccount.com",
  "client_id": "105996065829442454011",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/laimo-410%40brave-octane-261912.iam.gserviceaccount.com"
             }

credentials = ServiceAccountCredentials.from_json_keyfile_name(credential, scope)

gc = gspread.authorize(credentials)

wks = gc.open("laimotalk").sheet1

print(wks)

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
WEB_HOOK_LINKS = os.environ["SLACK_WEB_HOOKS_URL"]
BOT_OAUTH = os.environ["SLACK_BOT_OAUTH"]
POST_CHANEL_ID = os.environ["SLACK_POST_CHANEL_ID"]

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

memberlist = {"U386dbda4eb15a5a528c369f2efb19cbc": "薑薑", 
              "U6e7ed40306e372bf9fbf8b9ff246247b": "Karen Lai",
              "U7066e302325cdd755ae095c84752646b": "丁丁",
              "Ua341faf56eae4c42e5793d9c7c2db070": "Jaiden",
              "U1f3ff9f8bbc3737eb8a9338fc54b9092": "昀昀",
              "U2c9fd4e0ae312db9782043d84cdc54ec": "湯湯"
              }
 
slackMemberList = {"UQ1GM24ER": "ユウ/婉君", 
              "UQ1FPKX24": "hsu",
              "UPNN12QCA": "Evan",
              "UPQ33SVHR": "空 | Olga" 
              }

@app.route("/", methods=['POST'])
def callback():
    
    data = request.data.decode('utf-8')
    data = json.loads(data)
    
    print(data)
    if 'challenge' in data:
        token = str(data['challenge'])
        return Response(token, mimetype='text/plane')
    # for events which you added
    if 'event' in data:
        print("get event")
        event = data['event']
        if ("user" in event) and ("text" in event):
            print("user = ", event["user"])
            send_msg = slackMemberList.get(event["user"]) + "說\n" + event["text"]
       
    if 'events' in data:
      # get X-Line-Signature header value
      signature = request.headers['X-Line-Signature']

      # get request body as text
      body = request.get_data(as_text=True)
      app.logger.info("Request body: " + body)
    
      # handle web hook body
      try:
        handler.handle(body, signature)
      except InvalidSignatureError:
        abort(400)

    return Response("nothing", mimetype='text/plane')


def get_event_info(event):
    """
    トーク情報の取得
    :param event: LINE メッセージイベント
    :return: ユーザID, ユーザ表示名, 送信元トークルームの種別, ルームID
    :rtype: str, str, str, str
    """

    # LINEユーザー名の取得
    user_id = event.source.user_id
    try:
        user_name = line_bot_api.get_profile(user_id).display_name
    except LineBotApiError as e:
       user_name = memberlist.get(user_id, user_id)
    
    # トーク情報の取得
    if event.source.type == "user":
        msg_type = "個別"
        room_id = None
        return user_id, user_name, msg_type, room_id

    if event.source.type == "group":
        msg_type = "グループ"
        room_id = event.source.group_id
        return user_id, user_name, msg_type, room_id

    if event.source.type == "room":
        msg_type = "複数トーク"
        room_id = event.source.room_id
        return user_id, user_name, msg_type, room_id

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """
    Text Message の処理
    """

    slack_info = slackweb.Slack(url=WEB_HOOK_LINKS)

    # トーク情報の取得
    user_id, user_name, msg_type, room_id = get_event_info(event)

    # slack側に投稿するメッセージの加工
    send_msg = " {user_name}說\n".format(user_name=user_name) \
               + "{msg}\n".format(msg=event.message.text)  
    # メッセージの送信

    # replay_message = event

    slack_info.notify(text=send_msg)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    """
    Image Message の処理
    """

    # トーク情報の取得
    user_id, user_name, msg_type, room_id = get_event_info(event)

    # LINEで送信された画像の取得
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    img = message_content.content

    # slack側に投稿するメッセージの加工
    send_msg = "[bot-line] {user_name}さんが画像を送信しました．\n".format(user_name=user_name)

    file_name = "send_image_{message_id}".format(message_id=message_id)

    # 画像送信
    files = {'file': img}
    param = {
        'token': BOT_OAUTH,
        'channels': POST_CHANEL_ID,
        'filename': file_name,
        'initial_comment': send_msg,
        'title': file_name
    }
    response = requests.post(url="https://slack.com/api/files.upload", params=param, files=files)


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    """
    Sticker Message の処理
    """

    slack_info = slackweb.Slack(url=WEB_HOOK_LINKS)

    # トーク情報の取得
    user_id, user_name, msg_type, room_id = get_event_info(event)

    # LINEで送信されたスタンプ情報の取得
    package_id = event.message.package_id
    sticker_id = event.message.sticker_id

    # slack側に投稿するメッセージの加工
    send_msg = "[bot-line] {user_name}さんがスタンプを送信しました．\n".format(user_name=user_name) \
               + "package_id: {package_id}\n".format(package_id=package_id) \
               + "sticker_id: {sticker_id}\n".format(sticker_id=sticker_id) 

    # メッセージの送信
    slack_info.notify(text=send_msg)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
