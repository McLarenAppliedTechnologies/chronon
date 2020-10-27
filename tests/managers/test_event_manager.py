from chronon import EventManager
from chronon import ProcessManager
from chronon import Process

def test_create_user():
    pm = ProcessManager()

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            bene = True
    pm.attach_process(TestProcess1)

    em = EventManager(pm)
    em.create_user(f'user_test', instant=0)
    assert len(em.um._store) == 1

def test_run():
    pm = ProcessManager()

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            yield user.waits(5)
            print('va bene')
    pm.attach_process(TestProcess1)

    em = EventManager(pm)
    em.create_user(f'user_test')
    em.run()
