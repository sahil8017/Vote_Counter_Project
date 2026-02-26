# 🗳️ Vote Counter Project

A highly reliable, asynchronous vote counting system built with **FastAPI**, **RabbitMQ**, **Redis**, and **PostgreSQL**.

This project provides a robust architecture for receiving votes at high speed and processing them in the background without blocking the API response. It prevents race conditions using distributed locks, ensuring data integrity even under heavy concurrent load.

---

## 🏗 Architecture

The system is composed of five main components seamlessly orchestrated with **Docker Compose**:

1. **The API Door (FastAPI):** Receives incoming requests to create candidates or cast votes. When a vote is cast, it instantly pushes the task into a message queue rather than processing it synchronously.
2. **The Messenger (RabbitMQ):** Securely holds the vote tickets in a durable queue (`vote_queue`) until they can be processed by the background worker.
3. **The Bouncer (Redis):** Provides a distributed locking mechanism (`candidate_lock_{id}`). This ensures that even with massive concurrency, only one worker can update a specific candidate's vote count at a time, completely preventing race conditions.
4. **The Background Worker (Python/SQLAlchemy):** Concurrently consumes messages from RabbitMQ. It acquires a Redis lock for the target candidate, simulates a slow heavy-lifting process, safely increments the vote count in the database, and finally releases the lock.
5. **The Permanent Storage (PostgreSQL):** Safely stores candidates and tracks their aggregated vote counts.

<br>

## 🚀 Quick Start (Docker)

The absolute easiest way to get everything running is using Docker. It automatically provisions the Database, RabbitMQ, Redis, API, and the Background Worker.

### 1. Build and Run
```bash
# First time setup or when rebuilding images
docker-compose up --build

# For subsequent runs
docker-compose up
```

### 2. Services Running
Once Docker is up, the following services are available:
- **FastAPI application:** `http://localhost:8000`
- **RabbitMQ Management Dashboard:** `http://localhost:15672`
- **Redis Server:** `localhost:6379`
- **PostgreSQL Database:** `localhost:5432`

<br>

## 💻 Local Setup (Without Docker)

If you prefer to run the Python components locally (e.g., for direct development without rebuilding containers):

```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```
*(Note: You will still need RabbitMQ, Redis, and PostgreSQL running locally or via Docker, and you will need to adjust the connection strings in `app/main.py`, `app/worker.py`, and `app/database.py` if not using Docker DNS names).*

<br>

## 🔌 API Usage

### 1. Setup a Test Subject
Create a candidate who will receive the votes.

**Endpoint:** `POST /create-candidate`

**Parameters (Query):**
- `name` (string) - The name of the candidate.

**Using cURL:**
```bash
curl -X POST "http://localhost:8000/create-candidate?name=Alice"
```

**Expected Response:**
```json
{
  "id": 1,
  "name": "Alice",
  "votes": 0
}
```

### 2. The High-Speed Voter
Push a vote casting task to the system using the `/vote` endpoint.

**Endpoint:** `POST /vote`

**Parameters (Query):**
- `candidate_id` (integer) - The ID of the candidate you are voting for.

**Using cURL:**
```bash
curl -X POST "http://localhost:8000/vote?candidate_id=1"
```

**Expected Response:**
```json
{
  "status": "Vote Queued Successfully",
  "candidate_id": 1
}
```

<br>

## 🗄️ Checking the Database Manually

To verify the candidates and their current vote counts directly inside the PostgreSQL database, run these commands:

```bash
# 1. Access the PostgreSQL container interactively
docker exec -it vote_counter_project-db-1 psql -U user -d logs_db

# 2. Run the SQL query to view candidates and their votes
SELECT * FROM candidates;

# 3. Type \q to exit the psql prompt
```

You should see an output similar to this:
```text
 id | name  | votes 
----+-------+-------
  1 | Alice |    50
```

<br>

## 🛠 Tech Stack Details

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Extremely fast, modern web framework)
- **Message Broker:** [RabbitMQ](https://www.rabbitmq.com/) (Handles high-volume queueing and reliable delivery)
- **In-Memory Store / Lock:** [Redis](https://redis.io/) (Fast data store, acts as our distributed lock "Bouncer")
- **Database:** [PostgreSQL](https://www.postgresql.org/) (Robust relational DB)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/) (Database interactions)
- **Containerization:** [Docker & Docker Compose](https://www.docker.com/) (Isolated and easy deployment)
