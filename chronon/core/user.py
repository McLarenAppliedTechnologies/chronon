import simpy
from pandas import DataFrame, Series
from datetime import datetime, timedelta
from ..helpers.time import parse_time


class User:
    def __init__(self, pm, name, **kwargs):
        """
        Args:
            pm (:class:`.ProcessManager`)
            name (str)
            **kwargs: Arbitrary keyword arguments

        Keyword Args:
            instant (float/datetime): Instant when user enters the simulation. If not set, starts at 0.
            initial_process (str): Process in which the user enters the simulation.
                If not set, starts at flow's initial_process.

        Attributes:
            checkpoints (DataFrame): Report of occurence of key instants for this user
            env (:class:`simpy.Environment`): Environment linked to this manager
            pm (:class:`.ProcessManager`): :class:`.ProcessManager` linked to this manager
            rm (:class:`.ResourceManager`): :class:`.ResourceManager` linked to this manager
        """
        self.pm = pm
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

    def requests(self, resources_names):
        """Make user request resources.

        Args:
            resources_names (str): list of resources names to request

        Returns:
            :class:`simpy.Request`: list of requests
        """

        if isinstance(resources_names, str):
            resources_names = [resources_names]

        # Requests won't occupy a resource before all synched resources are available
        if len(resources_names) > 1:
            synched_resources = [self.rm.get_resource(r) for r in resources_names]
        else:
            synched_resources = None

        requests = []
        for r in resources_names:
            request = self.rm.get_resource(r).request(
                user=self, synched_resources=synched_resources)
            requests.append(request)
        return requests

    def releases(self, resources_names):
        """Make user release resources.
        If no request is specified, the oldest one using the resource will be realeased.

        Args:
            resources_names (str): list of resources names to release
        """
        if isinstance(resources_names, str):
            resources_names = [resources_names]

        for res in resources_names:
            # Releasing requests made by this user
            request_using = [req for req in self.rm.get_resource(
                res).users if req.user.name == self.name]
            request_queueing = [req for req in self.rm.get_resource(
                res).queue if req.user.name == self.name]
            if len(request_using) == 1:
                self.rm.get_resource(res).release(request_using[0])
            elif len(request_queueing) == 1:
                self.rm.get_resource(res).put_queue.remove(request_queueing[0])
            else:
                raise ValueError(
                    f'User {self.name} is not using or queueing on \
                    the Resource {self.rm.get_resource(res).name}'
                )

    def waits(self, something, **kwargs):
        """
        Make user wait for a specific time window to pass or wait for all
        resources in a list to be available

        Args:
            something (str): list of resources names to release or delay for timeout

        Keyword Args:
            patience (float/timedelta): maximum time user waits for obtaining the resources
        """
        patience = kwargs.get('patience', 'unlimited')

        # Patience
        if isinstance(patience, (int, float, datetime, timedelta)):
            waits_patience = self.env.timeout(parse_time(patience))
        elif patience == 'unlimited':
            # Creating an event that never will be triggered, aiming to make
            # patience_timeout neutral
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
            requests = self.requests(something)
            waits_time_or_resources = self.env.all_of(requests)

        return waits_time_or_resources | waits_patience

    def humanise(self, time):
        """Humanise datetime"""
        if isinstance(self.instant, datetime):
            time = datetime.fromtimestamp(time)
        else:
            time = time
        return time
