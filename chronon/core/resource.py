import simpy
from pandas import DataFrame, Series
from datetime import datetime


class Request(simpy.resources.base.Put):
    def __init__(self, resource, **kwargs):
        """Request usage of the *resource*. The event is triggered once access is
        granted. Subclass of :class:`simpy.resources.base.Put`.

        If the maximum capacity of users has not yet been reached, the request is
        triggered immediately. If the maximum capacity has been
        reached, the request is triggered once an earlier usage request on the
        resource is released.

        Args:
            resource (:class:`.Resource`): Resource to put the request

        Keyword Args:
            user (:class:`.User`): user putting the request
            synched_resources (list): list of :class:`.Resource` to be used in synchrony
        """
        super(simpy.resources.base.Put, self).__init__(resource._env)
        self.user = kwargs.get('user', None)
        self.resource = resource
        self.proc = self.env.active_process
        self.synched_resources = kwargs.get('synched_resources', None)

        # PUT queueing
        resource.put_queue.append(self)

        # Callback for triggering GET on this resource
        self.callbacks.append(resource._trigger_get)

        # Callbacks for triggering GET on all resources with queue and not at full
        # capacity
        resources_to_trigger = [
            r for r in resource.rm._store.values()
            if (len(r.users) < r.capacity) and (len(r.queue) > 0)
        ]
        for r in resources_to_trigger:
            self.callbacks.append(r._trigger_get)

        # Triggering PUT on this resource
        resource.update_usage(self.user, 'Requested')
        resource._trigger_put(None)

    def __exit__(self, exc_type, value, traceback):
        super().__exit__(exc_type, value, traceback)
        if exc_type is not GeneratorExit:
            self.resource.release(self)


class Release(simpy.resources.base.Get):
    def __init__(self, resource, request):
        """Releases the usage of *resource* granted by *request*. This event is
        triggered immediately. Subclass of :class:`simpy.resources.base.Get`.

        Args:
            resource (:class:`.Resource`): resource to release
            request (:class:`.Request`): request to release
        """
        super(simpy.resources.base.Get, self).__init__(resource._env)
        self.resource = resource
        self.request = request
        self.user = request.user
        self.proc = self.env.active_process

        # GET queueing
        resource.get_queue.append(self)

        # Callback for triggering PUT on this resource
        self.callbacks.append(resource._trigger_put)

        # Callbacks for triggering PUT on all resources with queue and not at full
        # capacity
        resources_to_trigger = [
            r for r in resource.rm._store.values()
            if (len(r.users) < r.capacity) and (len(r.queue) > 0)
        ]
        for r in resources_to_trigger:
            self.callbacks.append(r._trigger_put)

        # Triggering GET on this resource
        resource.update_usage(self.user, 'Released')
        resource._trigger_get(None)


class Resource(simpy.Resource):
    request = simpy.core.BoundClass(Request)
    release = simpy.core.BoundClass(Release)

    def __init__(self, rm, name, **kwargs):
        """Base resource class.

        Args:
            rm (:class:`.ResourceManager`): parent resource manager
            name (str): resource name
            **kwargs: Arbitrary keyword arguments
        """
        self.rm = rm
        self.name = name
        self.usage = DataFrame(columns=['instant', 'user', 'status', 'users', 'queue'])
        super().__init__(rm.env, **kwargs)

    def _trigger_put(self, get_event):
        idx = 0
        while idx < len(self.put_queue):
            put_event = self.put_queue[idx]
            self._do_put(put_event)
            if not put_event.triggered:
                idx += 1
            elif self.put_queue.pop(idx) != put_event:
                raise RuntimeError('Put queue invariant violated')

    def _do_put(self, event):
        if event.synched_resources:
            # Verifies if resources have enough capacity, excluding processes of this
            # user
            users = [r.users for r in event.synched_resources]
            this_user_processes = [
                len([s for s in u if s.user == event.user]) 
                for u in users
            ]
            resources_available = [
                len(r.users) < (r.capacity + s) 
                for r, s in zip(event.synched_resources, this_user_processes)
            ]
            if all(resources_available):
                self.users.append(event)
                event.usage_since = self._env.now
                event.succeed()
                self.update_usage(event.user, 'Using')
        else:
            if len(self.users) < self.capacity:
                self.users.append(event)
                event.usage_since = self._env.now
                event.succeed()
                self.update_usage(event.user, 'Using')

    def update_usage(self, user, status):
        """Update usage information"""
        users = [r.user.name for r in self.users]
        queue = [r.user.name for r in self.queue if r not in self.users]
        update = Series(data={
            'instant': user.humanise(self._env.now),
            'user': user.name,
            'status': status,
            'users': users,
            'queue': queue
        })
        self.usage = self.usage.append(update, ignore_index=True)
