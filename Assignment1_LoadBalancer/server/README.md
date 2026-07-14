# Distributed Load Balancer - Task 1: Server

## Overview

This project implements the **server component** of a distributed load balancing system for the Distributed Systems assignment.

The server is a lightweight Flask web application that exposes two REST API endpoints:

* `/home` – Returns the server identity.
* `/heartbeat` – Used by the load balancer to verify that the server is alive.

The server is designed to run inside a Docker container, allowing multiple replicas to be created easily by assigning different `SERVER_ID` values.

---

## Technologies Used

* Python 3
* Flask
* Docker

---

## Project Structure

```
server/
│── app.py
│── Dockerfile
│── requirements.txt
│── README.md
│── .gitignore
└── venv/
```

---

## Prerequisites

Before running the application, ensure you have the following installed:

* Python 3.11 or later
* pip
* Docker Desktop

---

## Installing Dependencies

Create and activate a virtual environment.

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
pip install -r requirements.txt
```

---

## Running the Server Locally

Set the server ID:

```powershell
$env:SERVER_ID="1"
```

Start the server:

```powershell
python app.py
```

The server will start on:

```
http://localhost:5000
```

---

## API Endpoints

### GET /home

Returns the identity of the running server.

**Request**

```
GET /home
```

**Response**

```json
{
    "message": "Hello from Server: 1",
    "status": "successful"
}
```

---

### GET /heartbeat

Health check endpoint used by the load balancer.

**Request**

```
GET /heartbeat
```

**Response**

* Status Code: **200 OK**
* Empty response body

---

## Docker

### Build the Docker Image

Navigate to the `server` directory and run:

```powershell
docker build -t distributed-server .
```

---

### Run the Docker Container

```powershell
docker run -d -p 5000:5000 -e SERVER_ID=1 --name server1 distributed-server
```

---

### Verify the Running Container

```powershell
docker ps
```

---

### View Container Logs

```powershell
docker logs server1
```

---

### Stop the Container

```powershell
docker stop server1
```

---

### Remove the Container

```powershell
docker rm server1
```

---

## Expected Output

Open the following URL in your browser:

```
http://localhost:5000/home
```

Expected response:

```json
{
    "message": "Hello from Server: 1",
    "status": "successful"
}
```

Health check:

```
http://localhost:5000/heartbeat
```

Returns:

* HTTP Status: **200 OK**
* Empty response body

---

## Environment Variable

| Variable  | Description                               | Example |
| --------- | ----------------------------------------- | ------- |
| SERVER_ID | Unique identifier for the server instance | 1       |

Each server replica should use a different `SERVER_ID`.

Example:

```
SERVER_ID=1
SERVER_ID=2
SERVER_ID=3
```

---

## Assignment Requirements Covered

This implementation satisfies the Task 1 requirements by:

* Implementing the `/home` endpoint.
* Implementing the `/heartbeat` endpoint.
* Running on port **5000**.
* Reading the server ID from an environment variable.
* Supporting Docker deployment for multiple server replicas.
