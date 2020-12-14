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

        Keyword Args:
            custom_resource (:class:): Custom resource class
        """
        ResourceClass = kwargs.get('custom_resource', Resource)

        if isinstance(names, str):
            names = [names]

        for n in names:
            self._store[n] = ResourceClass(self, n, **kwargs)

    def get_resource(self, name):
        """
        Get resource by name.

        Args:
            name (str)

        Returns:
            :class:`simpy.Resource`
        """
        return self._store[name]

    def get_resources(self, **kwargs):
        """
        Get resources by condition.

        Keyword Args:
            by_user (list): user or list of users who
                must be using any resources. Can be set to `any`.
            by_users_queueing (list): user or list of users
                who must be queueing in any of the resources.
                Can be set to `any`.
            by_properties (dict): dictionary with desired
                resources properties values.

        Returns:
            :class:`simpy.Resource`
        """
        by_user = kwargs.get('by_user', None)
        by_user_queueing = kwargs.get('by_user_queueing', None)
        by_properties = kwargs.get('by_properties', None)

        resources = []

        # All resources
        if by_user is None and by_user_queueing is None:
            resources = [self._store[k] for k in self._store.keys()]

        # Resources with users
        if by_user == 'any':
            resources += self.get_resources_with_users()

        # Resources specific users
        elif by_user is not None:
            if not isinstance(by_user, list):
                by_user = [by_user]
            for user in by_user:
                resources += self.get_resources_with_users(by_user=user)

        # Resources with queues
        if by_user_queueing == 'any':
            resources += self.get_resources_with_queues()

        # Resources with specific users on queues
        elif by_user_queueing is not None:
            if not isinstance(by_user_queueing, list):
                by_user_queueing = [by_user_queueing]
            for user in by_user_queueing:
                resources += self.get_resources_with_queues(by_user=user)

        resources = list(set(resources))

        # Resources filtered by property
        if by_properties is not None:
            resources = [
                r for r in resources if by_properties.items() <= r.__dict__.items()
            ]

        return resources

    def get_resources_with_users(self, by_user=None):
        if by_user is None:
            return [
                self.get_resource(r) for r in self.resources
                if len(self.get_resource(r).users) > 0
            ]
        else:
            # Supports both user and user.name
            return [
                self.get_resource(r) for r in self.resources
                if by_user in [request.user.name for request in self.get_resource(r).users]
                or by_user in [request.user for request in self.get_resource(r).users]
            ]

    def get_resources_with_queues(self, by_user=None):
        if by_user is None:
            return [
                self.get_resource(r) for r in self.resources
                if len(self.get_resource(r).queue) > 0
            ]
        else:
            # Supports both user and user.name
            return [
                self.get_resource(r) for r in self.resources
                if by_user in [request.user.name for request in self.get_resource(r).queue]
                or by_user in [request.user for request in self.get_resource(r).queue]
            ]
