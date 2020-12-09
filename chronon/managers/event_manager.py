from pandas import DataFrame, Series
from ..core.manager import Manager
from .user_manager import UserManager
from ..helpers.time import parse_time


class EventManager(Manager):
    def __init__(self, pm, **kwargs):
        """
        Manager for users.

        Args:
            pm (:class:`.ProcessManager`)

        Keyword Args:
            um (:class:`.UserManager`): If not set, a new :class:`.UserManager` is created

        Attributes:
            events (dict_keys): All events attached to this manager
            pm (:class:`.ProcessManager`): :class:`.ProcessManager` linked to this manager
            um (:class:`.UserManager`): :class:`.UserManager` linked to this manager
        """
        self.pm = pm
        super().__init__()
        self.um = kwargs.get('um', UserManager(pm))
        self.events = self._store.keys()
        self.checkpoints = DataFrame(columns=['instant', 'user', 'info'])

        # Setting flow for trivial one-process simulations
        if len(self.pm._store) == 1:
            self.pm.set_flow(sequence=list(self.pm._store.keys()))
        self.pm.block_flow()

        # Capturing flow inconsistencies
        if len(pm.flow[pm.flow['from'] == 'initial']) == 0:
            raise ValueError('No initial process was defined')
        if len(pm.flow[pm.flow['to'] == 'final']) == 0:
            raise ValueError('No final process was defined')

    def create_user(self, name, **kwargs):
        """
        Shortcut for `create_user` method in :class:`.UserManager`.
        """
        return self.um.create_user(name, **kwargs)

    def set_user(self, name, **kwargs):
        """
        Shortcut for `set_user` method in :class:`.UserManager`.

        Args:
            name (str)
            **kwargs: Arbitrary keyword arguments

        Keyword Args:
            instant (float): Instant when user enters the simulation. If not set, starts at 0.
            initial_process (str): Process in which the user enters the simulation.
                If not set, starts at flow's initial_process.
        """
        self.um.set_user(name, **kwargs)

    def get_user(self, name):
        """
        Shortcut for `get_user` method in :class:`.UserManager`.

        Args:
            name (str)

        Returns:
            :class:`.User`
        """
        return self.um.get_user(name)

    def run(self, **kwargs):
        """
        Create user processes and run simulation.
        """
        for user_name, user_object in self.um._store.items():
            self.pm.env.process(user_object.run())
        if 'until' in kwargs:
            kwargs['until'] = parse_time(kwargs['until'])
        self.pm.env.run(**kwargs)
        self.parse_checkpoints()

    def parse_checkpoints(self):
        """
        Combine checkpoints of all users in a time indexed data frame
        """
        for user in self.um.users:
            user_cp = self.um.get_user(user).checkpoints
            for index, row in user_cp.iterrows():
                user_row = Series(data={
                    'instant': row['instant'],
                    'user': user,
                    'info': row['info']
                })
                self.checkpoints = self.checkpoints.append(user_row, ignore_index=True)
                self.checkpoints = self.checkpoints.sort_values(
                    by='instant').reset_index(drop=True)
