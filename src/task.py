from enum import Enum
# from collections import deque


class TaskState(Enum):
    IDLE = 0,
    RUNNING = 1,
    DONE = 2,
    ERROR = -1


class ITask:
    ''' Task interface
    '''
    def __init__(self, _name: str, _continious: bool = False):
        self.status: TaskState = TaskState.IDLE
        self.handle: object = None
        self.continious: bool = _continious
        self.name: str = _name

    def Start(self):
        ''' Virtual method to be overidden
        '''
        pass

    def Stop(self):
        ''' Virtual method to be overidden
        '''
        pass

    def ReadData(self):
        ''' Virtual method to be overidden
        '''
        pass

    # def IsRunning(self):
    #     ''' Virtual method to be overidden
    #     '''
    #     pass

    # def IsDone(self):
    #     ''' Virtual method to be overidden
    #     '''
    #     pass

    # def Exception(self) -> Exception | None:
    #     ''' Virtual method to be overidden
    #     '''
    #     pass


class TaskHandler:
    def __init__(self, n_tasks: int):
        self.tasks: list[ITask] = []
        self.concurrent_tasks = n_tasks

    def Start(self, task: ITask) -> bool:
        ''' Virutal method to be overidden
        '''
        pass

    def Stop(self, task: ITask) -> bool:
        ''' Virtual method to be overidden
        '''
        pass

    def IsRunning(self, task: ITask) -> bool:
        ''' Virtual method to be overidden
        '''
        pass

    def IsDone(self, task: ITask):
        ''' Virtual method to be overidden
        '''
        pass

    def Exception(self, task: ITask) -> Exception | None:
        ''' Virtual method to be overidden
        '''
        pass
