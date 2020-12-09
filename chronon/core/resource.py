import simpy
from pandas import DataFrame, Series
from itertools import chain


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
            which (string): `all` or `any` resources in the list
            having (dict): properties that should match a specific value in the resources
        """
        super(simpy.resources.base.Put, self).__init__(resource._env)
        self.resource = resource
        self.proc = self.env.active_process

        # Parse all kwargs
        self.__dict__.update(kwargs)

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

        Keyword Args:
            capacity (int): resource capacity
        """
        self.rm = rm
        self.name = name
        self.__dict__.update(kwargs)
        self.usage = DataFrame(columns=['instant', 'user', 'status', 'users', 'queue'])
        super().__init__(rm.env, kwargs.get('capacity', 1))

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
        # Nomenclature warning: SimPy users are requests
        if event.synched_resources:
            # Assessing having conditional. True if resource matches required properties.
            having_condition = True
            if event.having is not None:
                for key, value in event.having.items():
                    having_condition = having_condition * \
                        (getattr(event.resource, key) == value)

            # Verify if resources have enough capacity, excluding processes of this user
            simpy_users = [
                r.users for r in event.synched_resources
            ]
            this_user_processes = [
                len([s for s in u if s.user == event.user])
                for u in simpy_users
            ]
            resources_available = [
                len(r.users) < (r.capacity + s)
                for r, s in zip(event.synched_resources, this_user_processes)
            ]

            # Get chronon users of all requests using any of the synched resources
            chronon_users = [
                u.user for u in list(chain.from_iterable(simpy_users))
            ]

            if (event.which == 'all'
                    and all(resources_available)
                    and having_condition):
                self.users.append(event)
                event.usage_since = self._env.now
                event.succeed()
                self.update_usage(event.user, 'Using')
            elif (event.which == 'any'
                    and event.user not in chronon_users
                    and event.resource.count < event.resource.capacity
                    and having_condition):
                self.users.append(event)
                event.usage_since = self._env.now
                event.succeed()
                self.update_usage(event.user, 'Using')
                # Remove this user from queues in other resources
                user_queues = self.rm.get_resources(by_user_queueing=event.user.name)
                event.user.releases([r.name for r in user_queues if r is not self])
                [r.update_usage(event.user, 'Unqueued') for r in user_queues if r is not self]

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
