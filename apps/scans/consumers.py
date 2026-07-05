"""Django Channels WebSocket consumer for real-time scan progress."""
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class ScanProgressConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket endpoint: WS /ws/scans/{scan_id}/

    Clients connect to receive live progress events for a specific scan.
    The Celery task pushes updates to the group; this consumer fans them
    out to all connected clients.
    """

    async def connect(self):
        """Join the scan-specific channel group on connection."""
        self.scan_id = self.scope["url_route"]["kwargs"]["scan_id"]
        self.group_name = f"scan_{self.scan_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("WS client connected to scan group %s", self.group_name)

    async def disconnect(self, close_code):
        """Leave the channel group on disconnect."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.debug("WS client disconnected from scan group %s (code=%s)", self.group_name, close_code)

    async def receive_json(self, content):
        """Clients do not send commands; ignore any incoming messages."""
        pass

    # ── Group message handlers ────────────────────────────────────────────

    async def scan_progress(self, event):
        """
        Forward a scan.progress group message to the WebSocket client.

        Event shape (sent by the Celery task):
        {
            "type": "scan.progress",
            "percent": 50,
            "status": "analyzing",
            "message": "Running Semgrep static analysis…"
        }
        """
        await self.send_json(
            {
                "type": "scan_progress",
                "scan_id": self.scan_id,
                "percent": event["percent"],
                "status": event["status"],
                "message": event["message"],
            }
        )
