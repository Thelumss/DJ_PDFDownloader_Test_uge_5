from task import ITask, TaskStatus


class LoggerTask(ITask):
    ''' Logger task
    Class for implementation of interface of ITask
    '''
    def __init__(self):
        super().__init__()

    def Start(self):
        self.status = TaskStatus.RUNNING

    def Stop(self):
        self.status = TaskStatus.DONE
