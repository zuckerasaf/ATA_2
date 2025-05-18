from typing import List
from datetime import datetime
from src.utils.test import Test

class TeslList:
    def __init__(self, tests: List[Test], timestamp: str = None, comment: str = "", numOfTest: int = 0, delay: int = 0):
        self.tests = tests  # List[Test]
        self.timestamp = timestamp if timestamp else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.comment = comment  # string
        self.numOfTest = numOfTest  # integer
        self.delay = delay  # integer (ms or s, depending on your use case)

    def add_test(self, test: Test):
        self.tests.append(test)
        self.numOfTest = len(self.tests)

    def to_dict(self):
        return {
            'tests': [t.to_dict() for t in self.tests],
            'timestamp': self.timestamp,
            'comment': self.comment,
            'numOfTest': self.numOfTest,
            'delay': self.delay
        }

    @classmethod
    def from_dict(cls, data):
        tests = [Test.from_dict(t) for t in data.get('tests', [])]
        return cls(
            tests=tests,
            timestamp=data.get('timestamp', None),
            comment=data.get('comment', ""),
            numOfTest=data.get('numOfTest', len(tests)),
            delay=data.get('delay', 0)
        ) 