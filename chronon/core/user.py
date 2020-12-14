import simpy
from pandas import DataFrame, Series
from datetime import datetime, timedelta
from ..helpers.time import parse_time


class User:
    def __init__(self, um, pm, name, **kwargs):
        """
        Args:
            um (:class:`.UserManager`)
            pm (:class:`.ProcessManager`)
            name (str)
            **kwargs: Arbitrary keyword arguments

        Keyword Args:
            instant (float/datetime): Instant when user enters the simulation.
                If not set, starts at 0.
            initial_process (str): Process in which the user enters the simulation.
                If not set, starts at flow's initial_process.

        Attributes:
            checkpoints (DataFrame): Report of occurence of key instants for this user
            env (:class:`simpy.Environment`): Environment linked to this manager
            pm (:class:`.ProcessManager`): :class:`.ProcessManager` linked to this manager
            rm (:class:`.ResourceManager`): :class:`.ResourceManager` linked to this manager
        """
        self.pm = pm
        self.um = um
        self.env = self.pm.env
        self.rm = self.pm.rm
        self.name = name
        self.__dict__.update(kwargs)
        self.instant = kwargs.get('instant', 0)
        self.initial_process = kwargs.get('initial_process', 'initial')
        self.checkpoints = DataFrame(columns=['instant', 'info'])

    def set_attributes(self, **kwargs):
        """
        Set user attributes

        Args:
            **kwargs: Arbitrary keyword arguments
        """
        self.__dict__.update(kwargs)

    def set_checkpoint(self, info):
        """
        Register key instants along the simulation

        Args:
            name (str): identifier of this checkpoint
        """
        checkpoint = Series(
            data={'instant': self.humanise(self.env.now), 'info': info}
        )
        self.checkpoints = self.checkpoints.append(checkpoint, ignore_index=True)

    def run(self):
        """Assemble timeline of events for a user."""
        yield self.pm.env.timeout(parse_time(self.instant))
        process = self.initial_process

        # Getting process being pointed by the initial tag
        if process == 'initial':
            process = self.pm.flow[self.pm.flow['from'] == process]['to'].values
            if len(process) > 1:
                raise ValueError(f'Next process is not uniquely defined: {process}')
            else:
                process = process[0]

        # Iterating processes
        while process != 'final':
            process_obj = self.pm.get_process(process)
            yield self.env.process(process_obj.definition(self))
            next_process = self.pm.flow[self.pm.flow['from'] == process]['to'].values
            if len(next_process) > 1:
                raise ValueError(
                    f'Next process is not uniquely defined: {next_process}')
            else:
                next_process = next_process[0]
            process = next_process

    def requests(self, resources, **kwargs):
        """Make user request resources.

        Args:
            resources (string/:class:`.Resource`): list of resources to request

        Keyword Args:
            which (string): `all` or `any` resources in the list
            having (dict): properties that should match a specific value in the resources

        Returns:
            :class:`simpy.Request`: list of requests
        """
        which = kwargs.get('which', 'all')
        having = kwargs.get('having', None)

        if not isinstance(resources, list):
            resources = [resources]

        # Retrieve resources if it's a request by name
        if isinstance(resources[0], str):
            resources = [self.rm.get_resource(r) for r in resources]

        # Requests won't occupy a resource before all synched resources are available
        if len(resources) > 1:
            synched_resources = resources
        else:
            synched_resources = None

        requests = []
        for r in resources:
            # If `any` stop making requests as soon as it gets access to a resource
            if which != 'any' or len(self.rm.get_resources(by_user=self.name)) == 0:
                request = r.request(
                    user=self,
                    synched_resources=synched_resources,
                    which=which,
                    having=having
                )
                requests.append(request)
        return requests

    def releases(self, resources):
        """Make user release resources.

        Args:
            resources (string/:class:`.Resource`): list of resources to release
        """

        if not isinstance(resources, list):
            resources = [resources]

        # Retrieve resources if it's a release by name
        if len(resources) > 0 and isinstance(resources[0], str):
            resources = [self.rm.get_resource(r) for r in resources]

        for res in resources:
            # Releasing requests made by this user
            request_using = [
                req for req in res.users
                if req.user == self
            ]
            request_queueing = [
                req for req in res.queue
                if req.user == self
            ]
            if len(request_using) == 1:
                res.release(request_using[0])
            elif len(request_queueing) == 1:
                res.put_queue.remove(request_queueing[0])
            else:
                raise ValueError(
                    f'User {self.name} is not using or queueing on \
                    the Resource {res.name}'
                )

    def waits(self, something, **kwargs):
        """
        Make user wait for a specific time window to pass or wait for all
        resources in a list to be available

        Args:
            something (int/string/:class:`.Resource`): delay for timeout or list
                of resources to request

        Keyword Args:
            patience (float/:class:`datetime.timedelta`): maximum time user waits
                for obtaining the resources
            which (string): `all` or `any` resources in the list
            having (dict): properties that should match a specific value in the resources
        """
        patience = kwargs.get('patience', 'unlimited')
        which = kwargs.get('which', 'all')
        having = kwargs.get('having', None)

        # Patience
        if isinstance(patience, (int, float, datetime, timedelta)):
            waits_patience = self.env.timeout(parse_time(patience))
        elif patience == 'unlimited':
            # Creating an event that never will be triggered, aiming to make
            # waits_patience neutral
            waits_patience = simpy.Event(self.env)
        else:
            raise ValueError('Patience must be a number or datetime object')

        # Timeout
        if isinstance(something, (int, float, datetime, timedelta)):
            waits_time_or_resources = self.env.all_of(
                [self.env.timeout(parse_time(something))]
            )

        # Resources
        else:
            requests = self.requests(something, which=which, having=having)
            if which == 'all':
                waits_time_or_resources = self.env.all_of(requests)
            elif which == 'any':
                waits_time_or_resources = self.env.any_of(requests)

        return waits_time_or_resources | waits_patience

    def humanise(self, time):
        """Humanise datetime"""
        if isinstance(self.instant, datetime):
            time = datetime.fromtimestamp(time)
        else:
            time = time
        return time

    def get_user(self, name):
        """
        Shortcut to Event Manager get_user
        """
        return self.um.get_user(name)
