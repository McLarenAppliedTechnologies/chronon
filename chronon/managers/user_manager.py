from ..core.manager import Manager
from ..core.user import User


class UserManager(Manager):
    def __init__(self, pm):
        """
        Args:
            pm (:class:`.ProcessManager`)

        Attributes:
            pm (:class:`.ProcessManager`): :class:`.ProcessManager` linked to this manager
            users (dict_keys): All users attached to this manager
        """
        self.pm = pm
        super().__init__()
        self.users = self._store.keys()

    def create_user(self, name, **kwargs):
        """
        Create a user in the process.

        Args:
            name (str)
            **kwargs: Arbitrary keyword arguments

        Keyword Args:
            instant (float): Instant when user enters the simulation. If not set, starts at 0.
            initial_process (str): Process in which the user enters the simulation.
                If not set, starts at flow's initial_process.
        """
        if isinstance(name, str):
            name = [name]
        for n in name:
            self._store[n] = User(self.pm, n, **kwargs)

    def get_user(self, name):
        """Get user by name.

        Args:
            name (str)

        Returns:
            :class:`.User`
        """
        return self._store[name]

    def set_user(self, name, **kwargs):
        """Set user attributes

        Args:
            name (str)
            **kwargs: Arbitrary keyword arguments

        Keyword Args:
            instant (float): Instant when user enters the simulation. If not set, starts at 0.
            initial_process (str): Process in which the user enters the simulation.
                If not set, starts at flow's initial_process.
        """

        self.get_user(name).set_attributes(**kwargs)
