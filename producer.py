import boto3
import json

ELASTIC_MQ_HOST = "http://localhost:9324"  # ElasticMQのホスト名
SAMPLE_QUEUE_NAME = "sample-queue"  # 送信先のキュー名、custom.confで定義したものを入力する
ACCOUNT_ID = "000000000000"  # ElasticMQの場合はこの値で固定
MESSAGE_SEND_COUNT = 15  # 送信するメッセージの数

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

# メッセージの作成
entities = []
for i in range(MESSAGE_SEND_COUNT):
    entities.append(
        {
            "Id": str(i),
            "MessageBody": "Message {}".format(i),
            "DelaySeconds": 0,  # 0秒後(=待機時間なし)でキューに入れる
        }
    )

# メッセージの送信
# 10件ずつ送信する
for i in range(0, len(entities), 10):
    response = sqs.send_message_batch(
        QueueUrl=queue_url,
        Entries=entities[i : i + 10],
    )
    print(f"Message sent result: {json.dumps(response, indent=2)}")
