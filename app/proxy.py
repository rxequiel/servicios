# example_consumer.py
import pika
import os
import csv
from analitica_modulo import analitica

while 1:
    url = os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()  # start a channel
    # channel.queue_declare(queue='mensajes') # Declare a queue

    def callback(ch, method, propperties, body):
        analitica().update_data(body.decode("utf-8"))
        return

    # set up subscription on the queue
    channel.basic_consume('mensajes', callback, auto_ack=True)

    # start consuming (blocks)
    channel.start_consuming()
    connection.close()
