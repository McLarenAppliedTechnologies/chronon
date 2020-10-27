from chronon import ProcessManager
from chronon import EventManager
from chronon import Process
import pytest


def test_create_resource():
    pm = ProcessManager()
    dummy_resource = ['test1', 'test2']
    pm.create_resource(dummy_resource)
    assert len(pm.rm._store) == 2


def test_attach_process():
    pm = ProcessManager()

    class TestProcess(Process):
        def definition(self, user, **kwargs):
            bene = True

    pm.attach_process(TestProcess)

    assert len(pm._store) == 1


def test_reset_flow():
    pm = ProcessManager()

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            va = True

    pm.attach_process(TestProcess1)

    class TestProcess2(Process):
        def definition(self, user, **kwargs):
            bene = True

    pm.attach_process(TestProcess2)

    pm.set_flow(sequence=('TestProcess1', 'TestProcess2'))
    pm.reset_flow()

    assert pm.flow.empty == True  # assert if dataframe is empty or not


def test_block_flow():
    pm = ProcessManager()

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            va = True

    pm.attach_process(TestProcess1)

    class TestProcess2(Process):
        def definition(self, user, **kwargs):
            bene = True

    pm.attach_process(TestProcess2)

    pm.block_flow()

    with pytest.raises(ValueError):
        assert pm.set_flow(sequence=('TestProcess1', 'TestProcess2'))


def test_unblock_flow():
    pm = ProcessManager()

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            va = True

    pm.attach_process(TestProcess1)

    class TestProcess2(Process):
        def definition(self, user, **kwargs):
            bene = True

    pm.attach_process(TestProcess2)

    pm.block_flow()
    pm.unblock_flow()
    pm.set_flow(sequence=('TestProcess1', 'TestProcess2'))


def test_set_flow_order_processes():
    pm = ProcessManager()

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            va = True

    pm.attach_process(TestProcess1)

    class TestProcess2(Process):
        def definition(self, user, **kwargs):
            bene = True

    pm.attach_process(TestProcess2)

    pm.set_flow(sequence=('TestProcess1', 'TestProcess2'))
    assert pm.flow['from'][1] == 'TestProcess1' and pm.flow['to'][1] == 'TestProcess2'


def test_set_flow_initial_final():
    pm = ProcessManager()

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            va = True

    pm.attach_process(TestProcess1)


    em = EventManager(pm)

    assert pm.flow['from'][0] == 'initial' and pm.flow['to'][1] == 'final'


def test_set_flow_cant_change_flow():
    pm = ProcessManager()

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            va = True

    pm.attach_process(TestProcess1)

    class TestProcess2(Process):
        def definition(self, user, **kwargs):
            bene = True

    pm.attach_process(TestProcess2)

    pm.set_flow(sequence=['TestProcess1', 'TestProcess2'])
    em = EventManager(pm)

    with pytest.raises(ValueError):
        pm.set_flow(sequence=['TestProcess2', 'TestProcess1'])


def test_set_flow_only_one_initial():
    pm = ProcessManager()

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            va = True

    pm.attach_process(TestProcess1)

    em = EventManager(pm)

    assert (pm.flow['from'] == 'initial').sum() == 1


def test_set_flow_need_sequence():
    pm = ProcessManager()

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            va = True

    pm.attach_process(TestProcess1)

    class TestProcess2(Process):
        def definition(self, user, **kwargs):
            bene = True

    pm.attach_process(TestProcess2)

    with pytest.raises(ValueError):
        em = EventManager(pm)

