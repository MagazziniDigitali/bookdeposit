redis: redis-server ./etc/redis.conf
celery: celery -l DEBUG -f logs/celery.log -A bookdeposit.process worker
flower: flower -A bookdeposit.process --port=5555
server: FLASK_DEBUG=1 FLASK_APP=bookdeposit/server.py flask run
