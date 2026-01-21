# engine/timer.py
import asyncio
import time

TURN_TIMEOUT = 30  # seconds

class TurnTimer:
    def __init__(self):
        self._tasks = {}

    async def start(self, room_id, on_timeout):
        """
        Start turn timer for a room.
        on_timeout = async callback(room_id)
        """
        self.cancel(room_id)

        async def _job():
            await asyncio.sleep(TURN_TIMEOUT)
            await on_timeout(room_id)

        task = asyncio.create_task(_job())
        self._tasks[room_id] = task

    def cancel(self, room_id):
        task = self._tasks.pop(room_id, None)
        if task and not task.done():
            task.cancel()

    def reset(self, room_id, on_timeout):
        self.cancel(room_id)
        return self.start(room_id, on_timeout)
      
