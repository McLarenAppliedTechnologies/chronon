from chronon import Process
from chronon import ProcessManager
from chronon import EventManager


def test_request():
    pm = ProcessManager()
    dummy_resource = ['test1']
    pm.create_resource(dummy_resource)

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            assert user.requests('test1')[0].triggered == True
            yield user.waits(1)

    pm.attach_process(TestProcess1)

    em = EventManager(pm)
    em.create_user('user_test')
    em.run()


def test_release():
    pm = ProcessManager()
    dummy_resource = ['test1']
    pm.create_resource(dummy_resource)

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            user.requests('test1')
            yield user.waits(1.2)
            user.releases('test1')

    pm.attach_process(TestProcess1)

    em = EventManager(pm)
    em.create_user('user_test')
    em.run()


def test_waits_unlimited_patience():
    pm = ProcessManager()
    dummy_resource = ['test1', 'test2']
    pm.create_resource(dummy_resource)

    class TestProcess1(Process):
        def definition(self, user, **kwargs):
            require = 'any'
            arrived = self.env.now
            yield user.waits(dummy_resource, require=require)
            now = self.env.now
            assert now - arrived == 0

    pm.attach_process(TestProcess1)

    em = EventManager(pm)
    em.create_user('user_test')
    em.run()
