import pika
import json
import time
import redis
from database import SessionLocal, Candidate

# 1. Connect to the Bouncer (Redis)
redis_client = redis.Redis(host='redis', port=6379, db=0)

def process_vote(candidate_id):
    db = SessionLocal()
    
    # 2. Define the exact lock name. We only want to lock THIS specific candidate.
    lock_name = f"candidate_lock_{candidate_id}"
    
    # 3. THE MAGIC: Acquire the lock. 
    # blocking_timeout=10 means "Wait up to 10 seconds in line if someone else is inside"
    try:
        with redis_client.lock(lock_name, blocking_timeout=10):
            print(f" [Worker] 🔒 Lock acquired for Candidate ID: {candidate_id}")
            
            # A. Look up the candidate
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                print(f" [Worker] ERROR: Candidate {candidate_id} not found.")
                return
            
            # B. Simulate a slow process (This is where a race condition normally destroys data!)
            print(f" [Worker] Reading current votes: {candidate.votes}. Calculating...")
            time.sleep(1) # We purposely slow it down to 1 second
            
            # C. Update the ledger
            candidate.votes += 1
            db.commit()
            print(f" [Worker] ✅ Vote added! New total: {candidate.votes}. Releasing lock 🔓")

    except redis.exceptions.LockError:
        print(f" [Worker] ⚠️ Could not get lock for Candidate {candidate_id}. Too busy!")
        # If we can't get the lock, the message goes back to RabbitMQ to try again later
        raise Exception("Failed to acquire lock")
        
    finally:
        db.close()

def on_message_received(ch, method, properties, body):
    data = json.loads(body)
    candidate_id = data.get("candidate_id")
    
    print(f"\n [Worker] Received vote ticket for Candidate ID: {candidate_id}")
    try:
        process_vote(candidate_id)
        # 4. Only acknowledge and delete the message if the lock and database save succeeded
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        # If it failed (like a lock timeout), we "NACK" it so RabbitMQ tries again
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

# 5. Connect to RabbitMQ (With startup wait loop)
def connect_to_rabbitmq():
    while True:
        try:
            return pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        except pika.exceptions.AMQPConnectionError:
            print(" [Worker] Waiting for RabbitMQ...")
            time.sleep(2)

connection = connect_to_rabbitmq()
channel = connection.channel()

channel.queue_declare(queue='vote_queue', durable=True)
channel.basic_qos(prefetch_count=1) # Don't take more than 1 ticket at a time
channel.basic_consume(queue='vote_queue', on_message_callback=on_message_received)

print(' [*] SentinelClear Vote Engine started. Waiting for votes...')
channel.start_consuming()