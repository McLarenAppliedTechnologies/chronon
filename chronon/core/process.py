class Process:
    def __init__(self, env, rm, name):
        """Base class for processes definitions.
        Should be extended overwriting `definition` method.

        Args:
            env (:class:`simpy.Environment`)
            rm (:class:`.ResourceManager`)
            name (str)
        """
        self.name = name
        self.env = env
        self.rm = rm

    def definition(self, user):
        """Definition method to be extended in custom processes.

        Args:
            user (:class:`.User`)
        """
        pass

    def get_resource(self, name):
        """
        Shortcut to Resource Manager get_resource
        """
        return self.rm.get_resource(name)

    def get_resources(self, **kwargs):
        """
        Shortcut to Resource Manager get_resources
        """
        return self.rm.get_resources(**kwargs)
