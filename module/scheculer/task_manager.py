import asyncio


class CoroTaskManager:
    def __init__(self):
        self.tasks = dict()    
        self.running = True    
        self.events = dict()   
        self.results = dict()


    async def add_task(self, task_id, task_coroutine):
        """Add new task, accept task ID and task coroutine"""
        event = asyncio.Event()
        self.events[task_id] = event

        async def wrapped_task():
            try:
                result = await task_coroutine
                self.results[task_id] = result
            except Exception as e:
                self.results[task_id] = e
            finally:
                event.set()

        task = asyncio.create_task(wrapped_task())
        self.tasks[task_id] = task


    async def wait_result(self, task_id, timeout):
        """Wait for task execution results"""
        event: asyncio.Event = self.events.pop(task_id, None)
        if event:
            try:
                await asyncio.wait_for(event.wait(), timeout)
                result = self.results.pop(task_id)
                if isinstance(result, Exception):
                    raise result
                return result
            except asyncio.TimeoutError:
                raise TimeoutError(f'Task {task_id} timed out after {timeout} seconds.')
        raise ValueError(f"Task {task_id} doesn't exist.")


    async def remove_completed_tasks(self):
        """Remove completed tasks
        TODO: Use database to store"""
        done, pending = await asyncio.wait(self.tasks.values(), return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            # Get task ID and results
            task_id, task_result = task.result()
            print(f'Task {task_id} is done!')

            # Remove tasks from dictionary
            for task_id, t in list(self.tasks.items()):
                if t == task:
                    task = self.tasks.pop(task_id)
                    break


    async def monitor_tasks(self):
        """Continuously monitor and clean up completed tasks until the end of the program."""
        while self.running:
            await asyncio.sleep(1)    # 每秒检查一次任务状态
            if self.tasks:
                await self.remove_completed_tasks()


    def start(self):
        """Start the coroutine for task monitoring
        Using a thread to run this coroutine can realize background scheduling of tasks. Examples are as follows:
        import asyncio
        from concurrent.futures import ProcessPoolExecutor

        async def add_new_task(task_manager, task_func, *args, **kwargs):
            ...

        async def main():
            loop = asyncio.get_running_loop()
            with ProcessPoolExecutor(4) as pool:
                task_manager = CoroTaskManager()
                
                # Start task monitoring
                monitor_task = task_manager.start()

                # Dynamically add tasks
                await add_new_task(task_manager, task_func, *args, **kwargs)
                await add_new_task(task_manager, task_func, *args, **kwargs)

                # Continue adding tasks after a delay
                await asyncio.sleep(2)
                await add_new_task(task_manager, task_func, *args, **kwargs)
                
                # Wait some time to observe the task execution
                await asyncio.sleep(10)

                # You can manually stop task monitoring, otherwise the task manager will keep running
                # task_manager.stop()

                # Wait for all tasks to complete
                await monitor_task

        """
        return asyncio.create_task(self.monitor_tasks())


    def stop(self):
        """Stop task monitoring"""
        self.running = False