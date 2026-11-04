"""Shutdown closes every service-owned resource even when one fails."""
import asyncio
import contextlib
import io
import unittest

import service


class ServiceShutdownTests(unittest.IsolatedAsyncioTestCase):
    async def test_failure_does_not_skip_later_stores(self):
        for failing_index in (0, 1):
            with self.subTest(failing_index=failing_index):
                closed = []
                failure = RuntimeError("injected close failure")

                class Resource:
                    def __init__(self, index):
                        self.index = index

                    async def close(self):
                        closed.append(self.index)
                        if self.index == failing_index:
                            raise failure

                with self.assertRaises(RuntimeError) as raised:
                    await service._close_resources(Resource(0), [Resource(1), Resource(2)])
                self.assertIs(raised.exception, failure)
                self.assertEqual(closed, [0, 1, 2])

    async def test_cancellation_is_propagated_after_stores_close(self):
        closed = []

        class Resource:
            def __init__(self, cancel=False):
                self.cancel = cancel

            async def close(self):
                closed.append(self.cancel)
                if self.cancel:
                    raise asyncio.CancelledError()

        with self.assertRaises(asyncio.CancelledError):
            await service._close_resources(Resource(True), [Resource(), Resource()])
        self.assertEqual(closed, [True, False, False])

    async def test_external_cancellation_closes_remaining_resources(self):
        started = asyncio.Event()
        closed = []

        class BlockedGoal:
            async def close(self):
                started.set()
                await asyncio.Event().wait()

        class Store:
            async def close(self):
                closed.append("closed")

        task = asyncio.create_task(service._close_resources(BlockedGoal(), [Store(), Store()]))
        await started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(closed, ["closed", "closed"])

    async def test_secondary_failure_is_reported(self):
        class Broken:
            def __init__(self, message):
                self.message = message

            async def close(self):
                raise RuntimeError(self.message)

        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            with self.assertRaisesRegex(RuntimeError, "first"):
                await service._close_resources(Broken("first"), [Broken("second")])
        self.assertIn("second", output.getvalue())
