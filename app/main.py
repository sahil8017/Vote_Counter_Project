from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import pika
import json

from database import SessionLocal, Candidate, Base, engine

# Create the tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint 1: Setup our test subject
@app.post("/create-candidate")
def create_candidate(name: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.name == name).first()
    if not candidate:
        candidate = Candidate(name=name, votes=0)
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
    return {"id": candidate.id, "name": candidate.name, "votes": candidate.votes}

# Endpoint 2: The High-Speed Voter
@app.post("/vote")
def cast_vote(candidate_id: int):
    # We instantly push the vote to RabbitMQ so the user isn't waiting
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='vote_queue', durable=True)

    payload = {"candidate_id": candidate_id}
    
    channel.basic_publish(
        exchange='',
        routing_key='vote_queue',
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

    return {"status": "Vote Queued Successfully", "candidate_id": candidate_id}