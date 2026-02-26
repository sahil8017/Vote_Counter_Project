# 📧 Email Blaster Project

A highly reliable, asynchronous email task processing system built with **FastAPI**, **RabbitMQ**, and **PostgreSQL**.

This project provides a robust architecture for receiving email requests and processing them in the background without blocking the API response, ensuring high throughput, state tracking, and resilience.

---

## 🏗 Architecture

The system is composed of four main components seamlessly orchestrated with **Docker Compose**:

1. **The API Door (FastAPI):** Receives the incoming email requests (recipient and message). It instantly logs the request in the database as `PENDING` and pushes the task ID into a message queue.
2. **The Messenger (RabbitMQ):** Holds the task IDs securely in a durable queue (`email_queue`) until they can be processed by a worker.
3. **The Background Worker (Python/SQLAlchemy):** Constantly consumes messages from RabbitMQ one-by-one. It updates the database state to `PROCESSING`, simulates sending the email (heavy lifting), and finally updates the state to `COMPLETED`.
4. **The Permanent Storage (PostgreSQL):** Safely stores all email tasks and tracks their real-time state.

<br>

## 🚀 Quick Start (Docker)

The absolute easiest way to get everything running is using Docker. It automatically provisions the Database, RabbitMQ, API, and the Background Worker.

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
*(Note: You will still need RabbitMQ and PostgreSQL running locally or via Docker, and you will need to adjust the connection strings in `app/main.py`, `app/worker.py`, and `app/database.py` if not using Docker DNS names).*

<br>

## 🔌 API Usage

### 1. Send an Email
You can push an email sending task to the system using the `/send-email` endpoint. 

**Endpoint:** `POST /send-email`

**Parameters (Query):**
- `recipient` (string) - The email address of the receiver.
- `message` (string) - The content of the email.

**Using cURL:**
```bash
curl -X POST "http://localhost:8000/send-email?recipient=john@example.com&message=Hello%20World"
```

**Expected Response:**
```json
{
  "status": "Accepted", 
  "task_id": 1,
  "state": "PENDING"
}
```

### 2. Check Task Status
You can check the real-time status of your email task (`PENDING`, `PROCESSING`, `COMPLETED`) using the task ID returned when you sent the email.

**Endpoint:** `GET /status/{task_id}`

**Using cURL:**
```bash
curl "http://localhost:8000/status/1"
```

**Expected Response:**
```json
{
  "task_id": 1,
  "recipient": "john@example.com",
  "current_state": "COMPLETED"
}
```

<br>

## 🗄️ Checking the Database Manually

To verify the email tasks directly inside the PostgreSQL database, run these commands:

```bash
# 1. Access the PostgreSQL container interactively
docker exec -it email_blaster_project-db-1 psql -U user -d logs_db

# 2. Run the SQL query to view saved tasks
SELECT * FROM email_tasks;

# 3. Type \q to exit the psql prompt
```

You should see an output similar to this:
```text
 id |    recipient     |   message   |  status   
----+------------------+-------------+-----------
  1 | john@example.com | Hello World | COMPLETED
```

<br>

## 🛠 Tech Stack Details

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Extremely fast, modern web framework)
- **Message Broker:** [RabbitMQ](https://www.rabbitmq.com/) (Handles high-volume queueing and reliable delivery)
- **Database:** [PostgreSQL](https://www.postgresql.org/) (Robust relational DB)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/) (Database interactions)
- **Containerization:** [Docker & Docker Compose](https://www.docker.com/) (Isolated and easy deployment)
