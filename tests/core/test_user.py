from chronon import Process
from chronon import ProcessManager
from chronon import EventManager
from datetime import datetime, timedelta
import pandas as pd


def test_wait_for_time():
    pm = ProcessManager()
    df = pd.DataFrame({'integer_test': [1], 'float_test': [1.1]})

    class TestProcess(Process):
        def definition(self, user):
            yield user.waits(1)
            yield user.waits(1.1)
            yield user.waits(df['integer_test'].values[0])
            yield user.waits(df['float_test'].values[0])
            yield user.waits(datetime(2021, 1, 1))
            yield user.waits(timedelta(minutes=1))
            user.set_checkpoint('Finished')

    pm.attach_process(TestProcess)
    em = EventManager(pm)
    em.create_user('user_test')
    em.run()
    assert em.checkpoints['instant'][0] == 1609459264.2
