<div align="center">

# 💬 YapZone

### Real-time conversations. Simple, fast, and built with Python.

A real-time one-to-one chat application powered by Django, Django Channels, WebSockets, and Redis.

<br/>

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge\&logo=django\&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST_Framework-API-A30000?style=for-the-badge\&logo=django\&logoColor=white)
![WebSockets](https://img.shields.io/badge/WebSockets-Realtime-5A45FF?style=for-the-badge)
![Redis](https://img.shields.io/badge/Redis-Memurai-DC382D?style=for-the-badge\&logo=redis\&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge\&logo=sqlite\&logoColor=white)

<br/>

**[View Repository](https://github.com/aadi-json/yapzone)**

</div>

---

# 📌 Table of Contents

* [About the Project](#-about-the-project)
* [Features](#-features)
* [Tech Stack](#-tech-stack)
* [How YapZone Works](#-how-yapzone-works)
* [Project Architecture](#-project-architecture)
* [Folder Structure](#-folder-structure)
* [Database Design](#-database-design)
* [API Endpoints](#-api-endpoints)
* [WebSocket Events](#-websocket-events)
* [Getting Started](#-getting-started)
* [Running Tests](#-running-tests)
* [Development Roadmap](#-development-roadmap)
* [Security](#-security)
* [Author](#-author)

---

# ✨ About the Project

**YapZone** is a real-time chat application built using Python and Django.

The goal of this project is to understand how modern messaging applications work internally, including real-time communication, WebSocket connections, user presence, message persistence, and asynchronous operations.

Unlike traditional HTTP requests, where the client sends a request and waits for a response, YapZone uses WebSockets to maintain persistent connections between users.

This allows users to exchange messages, receive online/offline updates, and see typing indicators instantly.

The project is being developed with scalability and clean backend architecture in mind.

---

# 🚀 Features

## ✅ Implemented Features

| Feature                     | Description                                                                               |
| --------------------------- | ----------------------------------------------------------------------------------------- |
| 🔐 User Authentication      | WebSocket connections are authenticated using Django REST Framework token authentication. |
| 👥 User Management          | Custom Django user model with profile information.                                        |
| 💬 One-to-One Conversations | Users can communicate through individual conversations.                                   |
| ⚡ Real-Time Messaging       | Messages are exchanged instantly using WebSockets.                                        |
| 💾 Message Persistence      | Messages are stored in the database.                                                      |
| 🟢 Online Presence          | Users are marked online when their first connection is established.                       |
| ⚫ Offline Presence          | Users are marked offline when their last active connection closes.                        |
| ✍️ Typing Indicators        | Participants can see when another user is typing.                                         |
| ⏱️ Automatic Typing Timeout | Typing status automatically stops after 3 seconds of inactivity.                          |
| 🔄 Typing Timeout Reset     | New typing events reset the previous timeout.                                             |
| 🔗 Multiple Connections     | Redis tracks multiple active WebSocket connections for a user.                            |

## 🚧 In Progress

* Message delivery receipts.
* Message read receipts.
* Improved connection and presence management.

## 🔮 Planned Features

* React frontend.
* PostgreSQL integration.
* Group conversations.
* Message editing and deletion.
* User profile management.
* Production deployment.

---

# 🧰 Tech Stack

The following technologies are currently used in the backend.

| Technology                    | Purpose                                                              |
| ----------------------------- | -------------------------------------------------------------------- |
| **Python 3.11**               | Main programming language.                                           |
| **Django 5.2**                | Backend framework for business logic, models, and routing.           |
| **Django REST Framework**     | Building REST APIs and implementing token authentication.            |
| **Django Channels**           | Extends Django to support WebSockets and asynchronous communication. |
| **WebSockets**                | Enables persistent, two-way communication between connected users.   |
| **Redis**                     | Stores active WebSocket connection information.                      |
| **Memurai**                   | Redis-compatible server used for local development on Windows.       |
| **SQLite**                    | Current database for storing users, conversations, and messages.     |
| **Python WebSockets Package** | Used to test WebSocket connections through Python scripts.           |
| **Git**                       | Version control.                                                     |
| **GitHub**                    | Source-code hosting and project management.                          |
| **PowerShell**                | Development environment and command execution on Windows.            |

### Planned Technologies

| Technology     | Planned Purpose                          |
| -------------- | ---------------------------------------- |
| **React.js**   | Frontend user interface.                 |
| **PostgreSQL** | Relational database for the application. |

> Note: React and PostgreSQL are planned technologies and are not yet implemented in the current backend.

---

# 🧠 How YapZone Works

## 1. Real-Time Messaging

YapZone uses Django Channels and WebSockets to exchange messages without repeatedly sending HTTP requests.

### Message Flow

```text
       USER A
          |
          | Sends a message
          |
          v
    WEBSOCKET CONNECTION
          |
          v
    DJANGO CHANNELS
          |
          | Validate message
          |
          | Save message
          v
      DATABASE
          |
          | Message persisted
          |
          v
    CHANNEL LAYER
          |
          | Broadcast event
          |
          v
   CONVERSATION GROUP
          |
          v
       USER B
          |
          | Receives message instantly
          v
       CHAT UI
```

### Step-by-step explanation

1. User A sends a message through an established WebSocket connection.
2. Django Channels receives the message.
3. The backend validates the message content.
4. The message is saved in the database.
5. Django Channels broadcasts the message to the conversation group.
6. All connected participants in that conversation receive the message.

---

## 2. Online/Offline Presence

YapZone uses Redis to track active WebSocket connections.

Each user can have multiple active connections.

For example:

```text
User: Aditya

Redis:

user:2:connections
    |
    |-- connection_1
    |
    |-- connection_2
```

### How it works

**When a user connects:**

1. The WebSocket connection is established.
2. The connection is registered in Redis.
3. If this is the user's first active connection, the user is marked online.
4. An online event is broadcast to the conversation.

**When a user disconnects:**

1. The connection is removed from Redis.
2. The remaining connection count is checked.
3. If no active connections remain, the user is marked offline.
4. An offline event is broadcast.

This prevents a user from being marked offline simply because one of their multiple connections closed.

---

## 3. Typing Indicators

Typing indicators allow users to know when another participant is typing.

### Example Event

When a user starts typing:

```json
{
    "type": "typing",
    "is_typing": true
}
```

The other participant receives:

```json
{
    "type": "typing",
    "user_id": 2,
    "username": "aditya",
    "is_typing": true
}
```

When the user stops typing:

```json
{
    "type": "typing",
    "is_typing": false
}
```

### Automatic Typing Timeout

YapZone implements an automatic 3-second typing timeout.

```text
0 seconds  → User starts typing
            → is_typing = true

2 seconds  → User sends another typing event
            → Previous timer cancelled
            → New timer starts

5 seconds  → No new typing event
            → is_typing = false
```

This ensures that typing indicators do not remain active indefinitely when a user stops typing without explicitly sending a stop event.

---

# 🏗️ Project Architecture

YapZone currently follows a Django backend architecture.

```text
                   CLIENT
                     |
          +----------+----------+
          |                     |
          v                     v
      REST APIs             WebSockets
          |                     |
          v                     v
    Django REST API       Django Channels
          |                     |
          |                     |
          v                     v
       DATABASE            CHANNEL LAYER
          |                     |
          |                     v
          |                   Redis
          |                     |
          |                     v
          |              Conversation Groups
          |                     |
          +---------------------+
```

### Main Components

| Component             | Responsibility                                                       |
| --------------------- | -------------------------------------------------------------------- |
| Django REST Framework | Handles HTTP APIs and token authentication.                          |
| Django Channels       | Manages WebSocket connections and events.                            |
| Redis                 | Stores active connection information and supports the channel layer. |
| SQLite                | Stores application data.                                             |
| Custom Middleware     | Authenticates WebSocket users using their tokens.                    |
| WebSocket Consumer    | Handles messaging, presence, and typing events.                      |

---

# 📁 Folder Structure

The current project is organized as follows:

```text
yapzone/
│
├── backend/
│   │
│   ├── chat/
│   │   ├── migrations/
│   │   │
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── consumers.py
│   │   ├── routing.py
│   │   ├── presence.py
│   │   ├── connection_manager.py
│   │   └── admin.py
│   │
│   ├── users/
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   ├── core/
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── token_auth.py
│   │   └── wsgi.py
│   │
│   ├── test_two_users.py
│   ├── test_presence.py
│   ├── test_typing.py
│   ├── test_typing_timeout.py
│   ├── test_typing_reset.py
│   │
│   ├── manage.py
│   ├── db.sqlite3
│   └── requirements.txt
│
├── README.md
└── .gitignore
```

*Note: This is the logical project structure. Some files may be added as development continues.*

### Important Files

| File                    | Responsibility                                                    |
| ----------------------- | ----------------------------------------------------------------- |
| `models.py`             | Defines database models such as Conversation and Message.         |
| `views.py`              | Handles REST API requests.                                        |
| `serializers.py`        | Converts model data into API responses and validates input.       |
| `consumers.py`          | Handles WebSocket connections and real-time events.               |
| `routing.py`            | Defines WebSocket URL patterns.                                   |
| `presence.py`           | Handles online/offline status updates.                            |
| `connection_manager.py` | Tracks active connections using Redis.                            |
| `asgi.py`               | Configures the ASGI application for HTTP and WebSocket protocols. |
| `token_auth.py`         | Authenticates WebSocket connections using DRF tokens.             |
| `settings.py`           | Contains Django application and service configuration.            |

---

# 🗄️ Database Design

YapZone currently uses SQLite for development.

### User Model

The application uses a custom Django user model.

Important fields include:

| Field       | Description                        |
| ----------- | ---------------------------------- |
| `username`  | Unique username.                   |
| `email`     | User email address.                |
| `password`  | Hashed password managed by Django. |
| `avatar`    | Profile image URL.                 |
| `bio`       | Short user description.            |
| `is_online` | Tracks online status.              |

### Conversation Model

Stores one-to-one conversations between two users.

| Field           | Description                      |
| --------------- | -------------------------------- |
| `id`            | Conversation identifier.         |
| `participant_1` | First participant.               |
| `participant_2` | Second participant.              |
| `created_at`    | Conversation creation timestamp. |

### Message Model

Stores messages exchanged in a conversation.

| Field          | Description                 |
| -------------- | --------------------------- |
| `id`           | Message identifier.         |
| `conversation` | Associated conversation.    |
| `sender`       | User who sent the message.  |
| `content`      | Message content.            |
| `timestamp`    | Message creation timestamp. |

Message delivery and read-status fields are being developed separately.

---

# 🔗 API Endpoints

The following REST endpoints are implemented in the current backend.

| Method | Endpoint                                      | Description                           |
| ------ | --------------------------------------------- | ------------------------------------- |
| GET    | `/api/`                                       | Backend home endpoint.                |
| GET    | `/api/health/`                                | Health-check endpoint.                |
| GET    | `/api/chat/conversations/`                    | Retrieves the user's conversations.   |
| POST   | `/api/chat/conversations/create/`             | Creates a conversation.               |
| GET    | `/api/chat/conversations/<id>/messages/`      | Retrieves conversation messages.      |
| POST   | `/api/chat/conversations/<id>/messages/send/` | Sends a message through the REST API. |

### Example: Create Conversation

```json
{
    "participant_id": 2
}
```

### Example: Send Message

```json
{
    "content": "Hello! Welcome to YapZone."
}
```

*The exact request fields depend on the serializer implementation.*

---

# 🔌 WebSocket Events

### WebSocket Connection

```text
ws://127.0.0.1:8000/ws/chat/<conversation_id>/
```

### 1. Send Message

**Client sends:**

```json
{
    "type": "message",
    "message": "Hello from YapZone!"
}
```

**Server broadcasts:**

```json
{
    "type": "message",
    "message_id": 1,
    "message": "Hello from YapZone!",
    "sender": "aditya",
    "timestamp": "2026-10-30T15:49:12.590545+00:00"
}
```

### 2. Typing Event

**Client sends:**

```json
{
    "type": "typing",
    "is_typing": true
}
```

**Server broadcasts:**

```json
{
    "type": "typing",
    "user_id": 2,
    "username": "aditya",
    "is_typing": true
}
```

### 3. Presence Event

**Server broadcasts:**

```json
{
    "type": "presence",
    "user_id": 2,
    "username": "aditya",
    "status": "online"
}
```

Possible status values:

* `online`
* `offline`

---

# ⚙️ Getting Started

Follow these instructions to run the current backend locally on Windows.

## Prerequisites

Make sure you have installed:

* Python 3.11
* Git
* Memurai or another Redis-compatible server
* PowerShell

## Step 1: Clone the Repository

```powershell
git clone https://github.com/aadi-json/yapzone.git
```

Navigate to the project:

```powershell
cd yapzone
cd backend
```

## Step 2: Create a Virtual Environment

```powershell
py -3.11 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Step 3: Install Dependencies

If `requirements.txt` exists:

```powershell
pip install -r requirements.txt
```

Otherwise, install the packages used by the current backend:

```powershell
pip install django djangorestframework channels channels-redis redis websockets
```

## Step 4: Start Redis

Start your Memurai service.

Make sure Redis is available at:

```text
127.0.0.1:6379
```

## Step 5: Apply Database Migrations

```powershell
python manage.py migrate
```

## Step 6: Start Django Server

```powershell
python manage.py runserver 8000
```

Your backend will be available at:

```text
http://127.0.0.1:8000/
```

Your WebSocket endpoint will be:

```text
ws://127.0.0.1:8000/ws/chat/<conversation_id>/
```

---

# 🧪 Running Tests

YapZone includes Python scripts to test its real-time functionality.

Keep the Django server and Redis service running.

### Step 1: Configure Authentication Tokens

In another PowerShell terminal, set the authentication tokens:

```powershell
$env:YAPZONE_USER_A_TOKEN = "YOUR_USER_A_TOKEN"

$env:YAPZONE_USER_B_TOKEN = "YOUR_USER_B_TOKEN"
```

Use your actual Django authentication tokens.

**Never commit these tokens to GitHub.**

### Step 2: Run the Tests

**Test real-time messaging:**

```powershell
python test_two_users.py
```

**Test online/offline presence:**

```powershell
python test_presence.py
```

**Test typing indicators:**

```powershell
python test_typing.py
```

**Test automatic typing timeout:**

```powershell
python test_typing_timeout.py
```

**Test typing timeout reset:**

```powershell
python test_typing_reset.py
```

### Tested Scenarios

| Test               | Expected Behavior                             |
| ------------------ | --------------------------------------------- |
| Two-user messaging | Both participants receive the same message.   |
| Presence           | Online/offline events are broadcast.          |
| Typing indicators  | Typing events reach the other participant.    |
| Automatic timeout  | Typing automatically stops after 3 seconds.   |
| Timeout reset      | A new typing event resets the previous timer. |

---

# 🗺️ Development Roadmap

YapZone is being developed incrementally.

### Backend

* [x] Django project setup.
* [x] Custom user model.
* [x] Conversation and message models.
* [x] REST API implementation.
* [x] Token-based authentication.
* [x] WebSocket authentication.
* [x] Real-time messaging.
* [x] Message persistence.
* [x] Multiple WebSocket connections.
* [x] Redis connection tracking.
* [x] Online/offline presence.
* [x] Typing indicators.
* [x] Automatic typing timeout.
* [x] Typing timeout reset.
* [ ] Message delivery receipts.
* [ ] Message read receipts.
* [ ] Improved connection recovery.

### Frontend

* [ ] React application.
* [ ] Login and registration pages.
* [ ] Conversation list.
* [ ] Real-time chat interface.
* [ ] Online/offline indicators.
* [ ] Typing indicators in UI.
* [ ] Message status indicators.

### Infrastructure

* [x] Local Redis-compatible service.
* [x] Git and GitHub integration.
* [ ] PostgreSQL integration.
* [ ] Production deployment.
* [ ] Docker configuration.

---

# 🔐 Security

Security is an important part of YapZone.

* WebSocket connections are authenticated using DRF tokens.
* Conversation membership is checked before allowing WebSocket access.
* Messages are validated before being saved.
* Authentication tokens must be kept private.
* Sensitive credentials should be stored in environment variables.
* `.env` files and database credentials should never be committed to GitHub.

The current Django development server is intended for local development, not production use.

---

# 🎯 Project Goals

Through YapZone, the main learning goals are:

* Understand how WebSockets work internally.
* Learn asynchronous programming with Django Channels.
* Understand Redis and connection management.
* Build real-time communication systems.
* Work with REST APIs and WebSocket authentication.
* Understand database relationships and message persistence.
* Learn how backend systems handle multiple concurrent connections.

---

# 👨‍💻 Author

<div align="center">

### Your one and only the GOAT Aditya Rekha Santosh Gawande

Python Developer | Backend Development | Software Engineering

<br/>

[![GitHub](https://img.shields.io/badge/GitHub-aadi--json-181717?style=for-the-badge\&logo=github)](https://github.com/aadi-json)

[![YapZone Repository](https://img.shields.io/badge/Project-YapZone-6C63FF?style=for-the-badge\&logo=github)](https://github.com/aadi-json/yapzone)

<br/>

**Built with Python, Django, and a lot of learning. 💜**

</div>
