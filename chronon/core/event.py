import simpy


class Event(simpy.Event):
    def __init__(self, env, name, **kwargs):
        """Base event class.

        Args:
            env (:class:`.simpy.Environment`)
            name (str)
            **kwargs: Arbitrary keyword arguments
        """
        self.name = name
        super().__init__(env, **kwargs)
