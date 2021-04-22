"""flask_line_receiver

LINE とのやりとりを行うスクリプトです。
"""

# Third-party modules.
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# User modules.
import utils
import consts

# このモジュール用のロガーを作成します。
logger = utils.get_my_logger(__name__)

app = Flask(__name__)

line_bot_api = LineBotApi(consts.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(consts.LINE_CHANNEL_SECRET)


# 必須ではないけれど、サーバに上がったことを確認するためにトップページを追加しておきます。
@app.route('/')
def top_page():
    # NOTE: logger でも Heroku ログにちゃんと出る。
    logger.debug('Here is root page.')
    return 'Here is root page.'


# ユーザがメッセージを送信したとき、この URL へアクセスが行われます。
@app.route('/callback', methods=['POST'])
def callback_post():

    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    logger.debug('Request body: ' + body)

    # NOTE: body の内容はこんな感じ。
    #       dict として扱い、値を取り出すこともできます。
    #       ただし handler によって add した関数内で利用するのが正道な気がする。
    # {
    #     "destination": "Uf2485b0560fd4931794caf4e4dab033d",
    #     "events": [
    #         {
    #             "type": "message",
    #             "message": {
    #                 "type": "text", "id": "13930066619344", "text": "HELLO"
    #             },
    #             "timestamp": 1619087553397,
    #             "source": {
    #                 "type": "group", "groupId": "C19709b8f8...acd9f538",
    #                 "userId": "U226ec6476abd.....e94a3fa9d3be56"
    #             },
    #             "replyToken": "f5bf4ee22dd54....4489279adb0",
    #             "mode": "active"
    #         }
    #     ]
    # }

    # handle webhook body
    try:
        # NOTE: ドキュメント https://github.com/line/line-bot-sdk-python#webhookhandler
        #       handler は、別途 @handler.add を定義することで利用する。
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


# NOTE: @handler.add した関数は、handler.handle 関数によって呼び出される、
#       ってイメージで多分 OK.
@handler.add(MessageEvent, message=TextMessage)
def on_get_message(event):

    # ここで行うことは……
    # - Push message を行うための送信先を取得。たぶん group id...??
    # - 誰の発言? を取得。(名前と user_id) user id は要らないか。
    # - メッセージの内容を取得。

    # Push message を行うための送信先。
    group_id = event.source.group_id
    print(dict(group_id=group_id))

    # 発言者の id。
    user_id = event.source.user_id
    # 発言者の情報。
    # NOTE: ドキュメント https://github.com/line/line-bot-sdk-python#get_profileself-user_id-timeoutnone
    user_profile = line_bot_api.get_profile(user_id)
    print(dict(
        display_name=user_profile.display_name,
        user_id=user_profile.user_id,
        picture_url=user_profile.picture_url,
        status_message=user_profile.status_message,
    ))

    # 返答するための token。
    # NOTE: line_bot_api.reply_message(reply_token, TextSendMessage(text='...')) と使用。
    reply_token = event.reply_token
    print(dict(reply_token=reply_token))

    # メッセージの内容。
    message_text = event.message.text
    print(dict(message_text=message_text))

    # TODO: 対象メッセージ(予想の書かれたメッセージ)かどうかを判別します。

    # TODO: 対象メッセージでなければ無視。

    # TODO: 対象メッセージであれば、 SpreadSheet への格納を行います。

    # TODO: どのレースの予想として格納されたか、発言者へ通知します。
    # NOTE: 「でないとどのレースの予想として扱われたのかわからないよね……」
    #       という意見が出たので、追加された機能です。そりゃそうだ。

    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=f'Send from line_bot_api.reply_message, you sent...: {message_text}')
    )


if __name__ == '__main__':
    app.run()
