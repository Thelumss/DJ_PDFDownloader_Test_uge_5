from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from functools import partial
from task import ITask, TaskState
from logger import Logger


class ITaskHandler(ABC):
    def __init__(self, n_tasks: int):
        self.tasks: list[ITask] = []
        self.concurrent_tasks = n_tasks
        self.active_tasks = 0

    @abstractmethod
    def Start(self, task: ITask, *args, **kvargs) -> bool:
        pass

    @abstractmethod
    def Stop(self, task: ITask) -> bool:
        ''' Virtual method to be overidden
        '''
        pass

    @abstractmethod
    def IsRunning(self, task: ITask) -> bool:
        ''' Virtual method to be overidden
        '''
        pass

    @abstractmethod
    def IsDone(self, task: ITask):
        ''' Virtual method to be overidden
        '''
        pass

    @abstractmethod
    def Exception(self, task: ITask) -> Exception | None:
        ''' Virtual method to be overidden
        '''
        pass

    @abstractmethod
    def ActiveTaskCount(self) -> int:
        pass


class ThreadPoolHandler(ITaskHandler):
    def __init__(self, n_tasks: int):
        super().__init__(n_tasks)
        self.executor = ThreadPoolExecutor(self.concurrent_tasks)
        self.running_tasks: list[ITask] = []

    def Start(self, task: ITask) -> bool:
        ''' Virutal method to be overidden
        '''
        try:
            task.handle = self.executor.submit(task.Start)
            task.handle.add_done_callback(partial(self.TaskDoneCB, task))
            self.running_tasks.append(task)
            # self.active_tasks = self.active_tasks + 1
            Logger().Trace((f" Task {task.name} started."
                            f"{len(self.running_tasks)} running."))
            return True
        except Exception as e:
            Logger().Error(f" Task {task.name} raised exception: {e}")
            return False

    def Stop(self, task: ITask) -> bool:
        ''' Virtual method to be overidden
        '''
        return task.handle.cancel()

    def IsRunning(self, task: ITask) -> bool:
        ''' Virtual method to be overidden
        '''
        return task.status == TaskState.RUNNING

    def IsDone(self, task: ITask):
        ''' Virtual method to be overidden
        '''
        return task.status == TaskState.DONE

    def Exception(self, task: ITask) -> Exception | None:
        ''' Virtual method to be overidden
        '''
        return task.handle.exception(timeout=0.5)

    def ActiveTaskCount(self) -> int:
        return len(self.running_tasks)

    def TaskDoneCB(self, task: ITask, future: Future):
        # for t in self.running_tasks:
        #     if t.name == task.name:
        task.Stop()
        self.running_tasks.remove(task)
        Logger().Trace((f" Task {task.name} stopped."
                        f" Running task(s) {len(self.running_tasks)}"))
