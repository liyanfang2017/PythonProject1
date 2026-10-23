# demo_kafka.py
# ## 4. Kafka（confluent‑kafka，同步示例；Kafka 库异步支持较弱）
#
# 特点：分区、高吞吐、海量消息堆积、多副本；适合日志流、大数据场景。
# > 需要本地启动 Kafka+Zookeeper，创建 topic：`order_topic`
# python demo_kafka.py producer
# python demo_kafka.py consumer

from confluent_kafka import Producer, Consumer, KafkaError

def producer():
    p = Producer({"bootstrap.servers":"127.0.0.1:9092"})
    def delivery_report(err, msg):
        if err:
            print(f"发送失败 {err}")
        else:
            print(f"[Kafka生产者]发送成功 topic={msg.topic()},partition={msg.partition()},offset={msg.offset()}")

    data = b'{"order_id":"ord_003","user_id":"u1003"}'
    p.produce("order_topic", value=data, on_delivery=delivery_report)
    p.flush()

def consumer():
    c = Consumer({
        "bootstrap.servers":"127.0.0.1:9092",
        "group.id":"order_kafka_group",
        "auto.offset.reset":"earliest"
    })
    c.subscribe(["order_topic"])
    print("[Kafka消费者启动]")
    while True:
        msg = c.consume(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                raise Exception(msg.error())
        print(f"[Kafka消费] offset={msg.offset()}, value={msg.value().decode()}")

if __name__ == "__main__":
    import sys
    if sys.argv[1] == "producer":
        producer()
    elif sys.argv[1] == "consumer":
        consumer()
