# S2-E Smoke Test - 13 Step End-to-End Test

## Task: Complete S2 Phase E smoke test on 165 server

### Environment Setup
1. Navigate to ~/dev/yixiaoguan-v2/services/gateway
2. Activate venv: source ~/dev/yixiaoguan-v2/venv/bin/activate
3. Set PYTHONPATH=.
4. Configure .env file with:
   - database_url=postgresql+asyncpg://yxg:yxg_v2_pass@localhost:5432/yixiaoguan_v2
   - redis_url=redis://:Yx%40Redis2026!@localhost:6379/1
   - dify_api_url=http://localhost:3000/v1
   - jwt_secret=change-me-in-production
5. Start FastAPI: python -m uvicorn app.main:app --host 0.0.0.0 --port 8100
6. Verify /health returns ok

### 13-Step Smoke Test
Execute these steps in order, saving tokens:

1. Student login: POST /api/auth/login with {" staff_id\:\2024010001\,\password\:\2024010001\}
2. Get user info: GET /api/auth/me with Authorization: Bearer {student_token}
3. Create conversation: POST /api/conversations with {\title\:\Test Conversation\}
4. Send message: POST /api/conversations/{conv_id}/messages with {\content\:\Hello how to apply for campus card?\}
5. Get messages: GET /api/conversations/{conv_id}/messages (should return 2 messages)
6. Escalate: POST /api/conversations/{conv_id}/escalate
7. Teacher login: POST /api/auth/login with {\staff_id\:\T001\,\password\:\liangshufeng\}
8. List conversations: GET /api/conversations (should show pending_teacher conversation)
9. Accept conversation: POST /api/conversations/{conv_id}/accept
10. Send teacher message: POST /api/conversations/{conv_id}/messages with {\content\:\Campus card is at Building A 1st floor\}
11. Resolve: POST /api/conversations/{conv_id}/resolve
12. Get full history: GET /api/conversations/{conv_id}/messages (should return 6 messages)
13. WebSocket test: Connect to ws://localhost:8100/ws?token={student_token}, send ping, expect pong

### Expected Results
- All HTTP calls return 200/201 status codes
- State transitions: ai_serving -> pending_teacher -> teacher_serving -> resolved
- System messages inserted for each transition
- WebSocket connection works with ping/pong
- GET /docs shows Swagger UI with all endpoints

### Report Format
Report each step with:
- Command executed
- Response status
- Key response data
- Pass/Fail status

