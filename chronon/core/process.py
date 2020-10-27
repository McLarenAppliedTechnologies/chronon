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
