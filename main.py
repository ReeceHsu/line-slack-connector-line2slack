import os

import requests
import slackweb
import json
import re
import datetime
import pytz
from flask import Flask, request, abort, Response
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, ImageMessage, StickerMessage, TextSendMessage

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('token.json', scope)

gc = gspread.authorize(credentials)


wks = gc.open("laimo02").sheet1


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
    if 'challenge' in data:
        token = str(data['challenge'])
        return Response(token, mimetype='text/plane')
    # for events which you added
    if 'event' in data:
        print("get event")
        event = data['event']
        if ("user" in event) and ("text" in event):
            print("user = ", event["user"])
             
            send_msg = slackMemberList.get(event["user"]) + "說\n" + event["text"] + "\n"+  datetime.datetime.now(pytz.timezone('Asia/Tokyo')).strftime("%H:%M:%S")
            amount_re = re.compile(r'說')
            cell = wks.findall(amount_re)
            finalcell = len(cell) + 1
            wks.update_acell("A"+str(finalcell) , send_msg)
       
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
    #wks.update_acell('A1', event.replyToken.value)
   
    #line_bot_api.reply_message(event.replyToken, '123')
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
   # wks.update_acell('A1', event.reply_token)
    #print(event)

    # replay_message = event
    
    slack_info.notify(text=send_msg)
    print(wks.col_values(1))
    wkslist = wks.col_values(1)
    listmsg = []
    if len(wkslist) >= 5:
        for i in range(5):
            listmsg.append(TextSendMessage(text=wks.col_values(1)[i]))
    elif len(wkslist) > 0 and len(wkslist) < 5:
        for item in wks.col_values(1):
            listmsg.append(TextSendMessage(text=item))
        
    if len(wkslist) >= 5:
      wks.delete_row(5)
      wks.resize(rows=50)
      print('ok')
      #clear data of 5 row
    elif len(wkslist) > 0 and len(wkslist) < 5:
      wks.clear()
      print('ook')

    line_bot_api.reply_message(event.reply_token, listmsg)
    
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
