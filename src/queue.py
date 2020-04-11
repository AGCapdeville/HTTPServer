class QueueMachine:
    def __init__(self):
        self.queueLine = []

    def enter_queue(self):
        if len(self.queueLine) < 10:
            if len(self.queueLine) != 0:
                if self.queueLine[0] == 1:
                    queueNumber = 0
                else:
                    queueNumber = len(self.queueLine)
            else:
                queueNumber = 0
            self.queueLine.append(queueNumber)
            return queueNumber
        else:
            return -1 
    
    def whos_turn(self):
        return self.queueLine[0]

    def exit_queue(self):
        self.queueLine.pop(0)
    
    def get_queue(self):
        return(self.queueLine)
  