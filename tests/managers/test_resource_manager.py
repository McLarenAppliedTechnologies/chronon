from chronon import ResourceManager
from chronon import Resource
import simpy


def test_create_resource():
    env = simpy.Environment
    rm = ResourceManager(env)
    dummy_resource = ['test1', 'test2']
    rm.create_resource(dummy_resource)
    assert len(rm._store) == 2


def test_get_resource():
    env = simpy.Environment
    rm = ResourceManager(env)
    dummy_resource = ['test1']
    rm.create_resource(dummy_resource)
    assert isinstance(rm.get_resource('test1'), Resource)
