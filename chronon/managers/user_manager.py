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
            custom_user (:class:): Custom user class
        """
        UserClass = kwargs.get('custom_user', User)

        if not isinstance(name, list):
            name = [name]

        users = []
        for n in name:
            self._store[n] = UserClass(self, self.pm, n, **kwargs)
            users.append(self._store[n])

        if len(users) == 1:
            users = users[0]

        return users

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
