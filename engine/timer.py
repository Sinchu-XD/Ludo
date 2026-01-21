# engine/timer.py
import asyncio
from typing import Callable, Dict

TURN_TIMEOUT = 30  # seconds


class TurnTimer:
    """
    One active timer per room.
    Safely cancels & restarts timers.
    """

    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}

    async def start(
        self,
        room_id: str,
        player_id: int,
        on_timeout: Callable[[str, int], None],
    ):
        """
        Start a turn timer for a room.

        on_timeout(room_id, player_id)
        """
        await self.cancel(room_id)

        async def _job():
            try:
                await asyncio.sleep(TURN_TIMEOUT)
                await on_timeout(room_id, player_id)
            except asyncio.CancelledError:
                # Timer cancelled safely
                pass

        task = asyncio.create_task(_job())
        self._tasks[room_id] = task

    async def cancel(self, room_id: str):
        """
        Cancel running timer for room
        """
        task = self._tasks.pop(room_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def reset(
        self,
        room_id: str,
        player_id: int,
        on_timeout: Callable[[str, int], None],
    ):
        """
        Reset timer safely
        """
        await self.cancel(room_id)
        await self.start(room_id, player_id, on_timeout)
