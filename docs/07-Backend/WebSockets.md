# WebSockets — Not Implemented in v1.0

## Current Status

WebSocket connections are **not implemented** in Covenexa v1.0.

## What Exists Instead

The Dashboard polls for new alerts on page mount:
```typescript
// DashboardPage.tsx
useEffect(() => {
  fetchAlerts();
}, [selectedCompanyId]);
```

Alerts are fetched via `GET /api/v1/alerts/?unread_only=true`.

## Planned for v1.1

Real-time push notifications for:
- New covenant breach alerts
- Pipeline completion events
- Health score changes

Implementation plan:
```python
# FastAPI WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket)
    # Subscribe to Redis channel → push to WebSocket
```

The `ConnectionManager` pattern (standard FastAPI WebSocket) will broadcast to all connected clients when the `AlertEngine` fires a new alert.
