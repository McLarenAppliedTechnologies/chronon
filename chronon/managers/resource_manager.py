from ..core.manager import Manager
from ..core.resource import Resource


class ResourceManager(Manager):
    def __init__(self, env):
        """
        Manager of resources.

        Args:
            env (:class:`simpy.Environment`)

        Attributes:
            env (:class:`simpy.Environment`): Environment linked to this manager
            resources (dict_keys): All resources attached to this manager
        """
        self.env = env
        super().__init__()
        self.resources = self._store.keys()

    def create_resource(self, names, **kwargs):
        """
        Args:
            names (str): List of names of resources to be created
            **kwargs: Arbitrary keyword arguments
        """
        if isinstance(names, str):
            names = [names]
        for n in names:
            self._store[n] = Resource(self, n, **kwargs)

    def get_resource(self, name):
        """
        Get resource by name.

        Args:
            name (str)

        Returns:
            :class:`simpy.Resource`
        """
        return self._store[name]
