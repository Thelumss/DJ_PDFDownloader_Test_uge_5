from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from functools import partial
import time
from task import ITask, TaskState
from logger import Logger


class ITaskHandler(ABC):
    """Interface to track and control ITasks and
    limit how many are running at the same time.
    """
    def __init__(self, n_tasks: int):
        self.tasks: list[ITask] = []
        self.concurrent_tasks = n_tasks
        self.active_tasks = 0

    @abstractmethod
    def Start(self, task: ITask, *args, **kvargs) -> bool:
        """Starts a task.
        Virtual function to be overridden.
        Args:
            task (ITask): [description]

        Returns:
            bool: true if task is started succesfully
        """
        pass

    @abstractmethod
    def Stop(self, task: ITask) -> bool:
        """  Signal task to stop
        Virtual method to be overidden

        Returns:
            bool: true if task is stopped succesfully
        """
        pass

    @abstractmethod
    def GetRunningTasks(self) -> list[ITask]:
        """ Returns a list of running tasks
        Virtual method to be overidden

        Returns:
            list[ITask]: running tasks
        """
        pass

    @abstractmethod
    def IsRunning(self, task: ITask) -> bool:
        """ Checks whether the task is running
        Virtual method to be overidden

        Returns:
            bool: true if running
        """
        pass

    @abstractmethod
    def IsDone(self, task: ITask):
        """ Check whether a task is completed
        Virtual method to be overidden

        Returns:
            bool: true if done
        """
        pass

    @abstractmethod
    def Exception(self, task: ITask) -> Exception | None:
        """ Check whether an exception occured on task
        Virtual method to be overidden

        Returns:
            Exception | None:
        """
        pass

    @abstractmethod
    def ActiveTaskCount(self) -> int:
        """The number of tasks that is running .

        Returns:
            int: active tasks
        """
        pass

    @abstractmethod
    def StopAllTasks(self):
        """Stops all Tasks .
        """
        pass


class ThreadPoolHandler(ITaskHandler):
    """ThreadPoolHandler class. implementation of ITaskHandler.
    """    
    def __init__(self, n_tasks: int):
        super().__init__(n_tasks)
        self.executor = ThreadPoolExecutor(self.concurrent_tasks)
        self.running_tasks: list[ITask] = []

    def Start(self, task: ITask) -> bool:
        """Override of interface
        """
        try:
            task.handle = self.executor.submit(task.Start)
            task.handle.add_done_callback(partial(self.TaskDoneCB, task))
            self.running_tasks.append(task)
            # self.active_tasks = self.active_tasks + 1
            Logger().Trace((f"Task {task.name} started."
                            f"{len(self.running_tasks)} running."))
            return True
        except Exception as e:
            Logger().Error(f"Task {task.name} raised exception: {e}")
            return False

    def Stop(self, task: ITask) -> bool:
        """Override of interface
        """
        task.Stop()
        return task.handle.cancel()

    def IsRunning(self, task: ITask) -> bool:
        """Override of interface
        """
        return task.status == TaskState.RUNNING

    def IsDone(self, task: ITask):
        """Override of interface
        """
        return task.status == TaskState.DONE

    def Exception(self, task: ITask) -> Exception | None:
        """Override of interface
        """
        return task.handle.exception(timeout=0.5)

    def ActiveTaskCount(self) -> int:
        """Override of interface
        """
        return len(self.running_tasks)

    def GetRunningTasks(self) -> list[ITask]:
        """Override of interface
        """
        return self.running_tasks

    def StopAllTasks(self):
        """Override of interface.
        Blocking function waiting for all task to finish
        """
        # Signal to stop
        for task in self.running_tasks:
            self.Stop(task)
        # Wait for tasks to stop
        while self.ActiveTaskCount() > 0:
            time.sleep(0.1)

    def TaskDoneCB(self, task: ITask, future: Future):
        """Override of interface
        """
        task.Stop()
        self.running_tasks.remove(task)
        Logger().Trace((f"Task {task.name} stopped. Duration: "
                        f"{task.timer.DurationMS():.1f} (ms)."
                        f" Running task(s) {len(self.running_tasks)}"))
