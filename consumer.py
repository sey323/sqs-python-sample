import random
import time
import boto3
import json

ELASTIC_MQ_HOST = "http://localhost:9324"  # ElasticMQのホスト名
SAMPLE_QUEUE_NAME = "sample-queue"  # 送信先のキュー名、custom.confで定義したものを入力する
ACCOUNT_ID = "000000000000"  # ElasticMQの場合はこの値で固定
MESSAGE_RECEIVE_COUNT = 10  # 受信するメッセージの数

# SQSクライアントの作成
session = boto3.session.Session()
sqs = session.client(
    "sqs",
    endpoint_url=ELASTIC_MQ_HOST,  # SQSのエンドポイントを指定
    region_name="us-east-1",  # ElasticMQはリージョン,資格情報ををチェックしないが、boto3に必要なので適当に指定
    aws_access_key_id="x",
    aws_secret_access_key="x",
    verify=False,
)

# Queue URLの作成
queue_url = f"{ELASTIC_MQ_HOST}/{ACCOUNT_ID}/{SAMPLE_QUEUE_NAME}"
print(f"Queue URL: {queue_url}")

# コンシューマー処理
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=MESSAGE_RECEIVE_COUNT,  # ①バッチ処理: 10件ずつメッセージを取得
    WaitTimeSeconds=20,  # ②ロングポーリング: 20秒間メッセージを取得できなかったら、空のレスポンスを返す
)

if "Messages" in response:
    remaining_messages = response["Messages"].copy()
    print(f"受信したメッセージの数: {len(remaining_messages)}")
    for message in response["Messages"]:
        try:
            time.sleep(1)
            # ランダムでエラーを発生させる
            if random.randint(0, 9) == 0:
                raise Exception("エラーが発生しました。")

            print(f"受信したメッセージの結果: {json.dumps(message, indent=2)}")

            # ③メッセージを処理した後、再処理しないようにキューから削除
            receipt_handle = message["ReceiptHandle"]
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

            # messagesから削除
            remaining_messages.remove(message)
        except Exception:
            print("エラーが発生しました。メッセージをキューに返却します。")
            # ④エラーが発生した場合にメッセージをキューに返却
            sqs.change_message_visibility(
                QueueUrl=queue_url,
                ReceiptHandle=message["ReceiptHandle"],
                VisibilityTimeout=0,  # 0秒後に再処理する
            )
            # messagesから削除
            remaining_messages.remove(message)
        except KeyboardInterrupt:
            print(
                f"キーボード割り込みが発生しました。 処理中のメッセージをキューに返却します: {[message['MessageId'] for message in remaining_messages]}"
            )

            # ⑤強制終了(KeybordeInterrupt)が発生した場合に未処理のメッセージをキューに返却
            entities = [
                {
                    "Id": message["MessageId"],
                    "ReceiptHandle": message["ReceiptHandle"],
                    "VisibilityTimeout": 0,  # 0秒後に再処理することで即座に他のコンシューマーが処理できるようにする
                }
                for message in remaining_messages
            ]
            response = sqs.change_message_visibility_batch(
                QueueUrl=queue_url, Entries=entities
            )
            print(f"{len(entities)}件のメッセージをキューに返却しました。")
            exit(1)
