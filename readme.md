# TaskPilot – AI Task Management Agent

**QuantumApps AI – AI Engineer (Full Stack) Take-Home Assignment | Round 1 | Project B**

TaskPilot is a full-stack AI-powered task management application that allows users to manage their tasks through natural-language conversations with an AI agent. The agent uses LLM function calling to create, list, update, and delete tasks, including multi-step operations.

The application includes JWT-based authentication, role-based access control, a PostgreSQL database, and a responsive web interface.

## 🚀 Live Application

- **Frontend URL:** https://taskpilot-g5l3.onrender.com
- **Backend URL:** https://taskpilot-g5l3.onrender.com
- **API Documentation:** https://taskpilot-g5l3.onrender.com/docs
- **GitHub Repository:** https://github.com/Vishesh-OP/-taskpilot

**Hosting note:** The backend uses Render's free tier. It may spin down after 15 minutes of inactivity. The first request after inactivity can take approximately 50–60 seconds to respond.

## 🔐 Demo Login Credentials

Use these dedicated demo accounts to test the application.

| Role | Email | Password |
|---|---|---|
| Admin | [dmin@taskpilot.com] | [Admin@1234] |
| User | [user@taskpilot.com] | [User@1234] |

These should be working demo accounts created specifically for evaluation.

## ✨ Key Features

- AI-powered task management through natural-language chat.
- Create, view, update, and delete tasks.
- LLM function/tool calling.
- Multi-step task execution.
- User registration and login.
- JWT-based authentication.
- Role-based access control (Admin and User).
- User-specific task management.
- Admin access to users and tasks.
- Persistent PostgreSQL database.
- Interactive task dashboard.

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | Python 3.11, FastAPI |
| ORM | SQLAlchemy |
| AI / LLM | Groq API |
| LLM Model | llama-3.1-8b-instant |
| Database | PostgreSQL (Neon) |
| Authentication | JWT |
| Password Hashing | bcrypt |
| API Documentation | FastAPI / Swagger |
| Frontend Hosting | Render |
| Backend Hosting | Render |

## 🤖 How the AI Agent Works

1. The user enters a natural-language request through the chat interface.
2. The frontend sends the request to the FastAPI backend.
3. The backend sends the conversation and available tool definitions to the Groq LLM.
4. The LLM identifies the appropriate function calls, such as `add_task`, `list_tasks`, `update_task`, or `delete_task`.
5. The backend validates and executes the requested operations against PostgreSQL.
6. Tool results are returned to the LLM, which generates a natural-language response.
7. The frontend displays the response and updated task information.

The agent supports multi-step requests, such as completing an existing task and creating a new task in the same conversation.

## 🔑 Authentication and Role-Based Access Control

TaskPilot uses JWT authentication and bcrypt password hashing.

**Admin Role**
- View registered users.
- View tasks across users.
- Access administrative functionality.

**User Role**
- Create and manage personal tasks.
- View only their own tasks.
- Interact with the AI task management agent.

New registrations receive the normal `user` role by default. Administrative permissions are enforced on the backend rather than relying only on frontend visibility.

## 💻 Running the Project Locally

### Prerequisites

- Python 3.11+
- Node.js and npm
- PostgreSQL database
- Groq API key
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Vishesh-OP/-taskpilot.git
cd -taskpilot
```

### 2. Backend setup

```bash
cd backend

python -m venv .venv
```

Activate the virtual environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file using the variable names from `.env.example` and configure your own credentials.

Start the backend using the same FastAPI module path configured in the deployment:

```bash
uvicorn YOUR_MODULE_PATH:app --reload
```

The API documentation will be available at:

`http://localhost:8000/docs`

### 3. Frontend setup

Open another terminal:

```bash
cd frontend

npm install
```

Configure the frontend API URL in the frontend environment file:

```env
VITE_API_URL=http://localhost:8000
```

Use the exact environment variable name expected by the frontend source code.

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

`http://localhost:5173`

## ⚙️ Environment Variables

The application uses environment variables for configuration.

Backend variables include:

- `DATABASE_URL`
- `JWT_SECRET`
- `GROQ_API_KEY`
- `GROQ_MODEL`
- `ADMIN_PASSWORD`
- `DEMO_PASSWORD`

Frontend variable:

- `VITE_API_URL`

Never commit real API keys, database credentials, JWT secrets, or production passwords to GitHub. Use `.env.example` with placeholder values.

## 🔮 Future Improvements

- Task reminders and notifications.
- Task priorities and categories.
- Improved AI conversation history.
- More advanced multi-step agent workflows.
- Automated testing and monitoring.
- Improved error handling and user feedback.

## 👨‍💻 Project Information

**Project:** TaskPilot – AI Task Management Agent  
**Assignment:** QuantumApps AI – AI Engineer (Full Stack), Round 1  
**Selected Project:** Project B – TaskPilot  
**Developer:** Vishesh

