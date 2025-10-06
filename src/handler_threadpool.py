from task import TaskHandler, ITask
from concurrent.futures import ThreadPoolExecutor
from logger import Logger


class ThreadPoolHandler(TaskHandler):
    def __init__(self, n_tasks: int):
        super().__init__(n_tasks)
        self.executor = ThreadPoolExecutor(self.concurrent_tasks)

    def Start(self, task: ITask) -> bool:
        ''' Virutal method to be overidden
        '''
        try:
            task.handle = self.executor.submit(task.Start)
            self.tasks.append(task)
            Logger().Trace(f"Task {task.name} started")
            return True
        except Exception as e:
            Logger().Error(f"Task {task.name} raised exception: {e}")
            return False

    def Stop(self, task: ITask) -> bool:
        ''' Virtual method to be overidden
        '''
        return task.handle.cancel()

    def IsRunning(self, task: ITask) -> bool:
        ''' Virtual method to be overidden
        '''
        return task.handle.running()

    def IsDone(self, task: ITask):
        ''' Virtual method to be overidden
        '''
        return task.handle.done()

    def Exception(self, task: ITask) -> Exception | None:
        ''' Virtual method to be overidden
        '''
        return task.handle.exception(timeout=0.5)
