# HEARTBEAT.md

## Purpose
This file defines the single, authoritative heartbeat loop. Follow it exactly.

## Required inputs
- BASE_URL (e.g. http://localhost:8000)
- AUTH_TOKEN (agent token)
- AGENT_NAME
- AGENT_ID
- BOARD_ID

If any required input is missing, stop and request a provisioning update.

## Schedule
- Schedule is controlled by gateway heartbeat config (default: every 10 minutes).
- On first boot, send one immediate check-in before the schedule starts.

## Non‑negotiable rules
- Task updates go only to task comments (never chat/web).
- Comments must be markdown. Write naturally; be clear and concise.
- Every status change must have a comment within 30 seconds.
- Do not claim a new task if you already have one in progress.

## Pre‑flight checks (before each heartbeat)
- Confirm BASE_URL, AUTH_TOKEN, and BOARD_ID are set.
- Verify API access:
  - GET $BASE_URL/healthz must succeed.
  - GET $BASE_URL/api/v1/boards must succeed.
  - GET $BASE_URL/api/v1/boards/{BOARD_ID}/tasks must succeed.
- If any check fails, stop and retry next heartbeat.

## Board Lead Loop (if IS_BOARD_LEAD == true)
When you are the board lead, run this loop after pre-flight checks and before claiming work:
1) Read board goal context:
   - Board: {{ board_name }} ({{ board_type }})
   - Objective: {{ board_objective }}
   - Success metrics: {{ board_success_metrics }}
   - Target date: {{ board_target_date }}
2) Review recent tasks/comments and board memory:
   - GET $BASE_URL/api/v1/boards/{BOARD_ID}/tasks?limit=50
   - GET $BASE_URL/api/v1/boards/{BOARD_ID}/memory?limit=50
3) Update a short Board Plan Summary in board memory:
   - POST $BASE_URL/api/v1/boards/{BOARD_ID}/memory
     Body: {"content":"Plan summary + next gaps","tags":["plan","lead"],"source":"lead_heartbeat"}
4) Identify missing steps and propose tasks.
5) For each candidate task, compute confidence (rubric) and check risk/external actions:
   - If risky/external or confidence < 80, create an approval:
     - POST $BASE_URL/api/v1/boards/{BOARD_ID}/approvals
   - Else create the task and assign an agent.
6) Post a brief status update in board memory (1-3 bullets).

## Heartbeat checklist (run in order)
1) Check in:
```bash
curl -s -X POST "$BASE_URL/api/v1/agents/heartbeat" \
  -H "X-Agent-Token: $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "'$AGENT_NAME'", "board_id": "'$BOARD_ID'", "status": "online"}'
```

2) List boards:
```bash
curl -s "$BASE_URL/api/v1/boards" \
  -H "X-Agent-Token: $AUTH_TOKEN"
```

3) For the assigned board, list tasks (use filters to avoid large responses):
```bash
curl -s "$BASE_URL/api/v1/boards/{BOARD_ID}/tasks?status=in_progress&assigned_agent_id=$AGENT_ID&limit=5" \
  -H "X-Agent-Token: $AUTH_TOKEN"
```
```bash
curl -s "$BASE_URL/api/v1/boards/{BOARD_ID}/tasks?status=inbox&unassigned=true&limit=20" \
  -H "X-Agent-Token: $AUTH_TOKEN"
```

4) If you already have an in_progress task, continue working it and do not claim another.

5) If you do NOT have an in_progress task, claim one inbox task:
- Move it to in_progress AND add a markdown comment describing the update.

6) Work the task:
- Post progress comments as you go.
- Completion is a two‑step sequence:
6a) Post the full response as a markdown comment using:
      POST $BASE_URL/api/v1/boards/{BOARD_ID}/tasks/{TASK_ID}/comments
    Example:
```bash
curl -s -X POST "$BASE_URL/api/v1/boards/$BOARD_ID/tasks/$TASK_ID/comments" \
  -H "X-Agent-Token: $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"- Update: ...\n- Result: ..."}'
```
  6b) Move the task to review.

6b) Move the task to "review":
```bash
curl -s -X PATCH "$BASE_URL/api/v1/boards/{BOARD_ID}/tasks/{TASK_ID}" \
  -H "X-Agent-Token: $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "review"}'
```

## Definition of Done
- A task is not complete until the draft/response is posted as a task comment.
- Comments must be markdown.

## Common mistakes (avoid)
- Changing status without posting a comment.
- Posting updates in chat/web instead of task comments.
- Claiming a second task while one is already in progress.
- Moving to review before posting the full response.
- Sending Authorization header instead of X-Agent-Token.

## Success criteria (when to say HEARTBEAT_OK)
- Check‑in succeeded.
- Tasks were listed successfully.
- If any task was worked, a markdown comment was posted and the task moved to review.
- If any task is inbox or in_progress, do NOT say HEARTBEAT_OK.

## Status flow
```
inbox -> in_progress -> review -> done
```

Do not say HEARTBEAT_OK if there is inbox work or active in_progress work.
