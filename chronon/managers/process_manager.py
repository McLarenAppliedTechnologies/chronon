import simpy
import warnings
from pandas import DataFrame
from ..core.manager import Manager
from .resource_manager import ResourceManager


class ProcessManager(Manager):
    def __init__(self, **kwargs):
        """
        Manager of processes.

        Keyword Args:
            rm (:class:`.ResourceManager`): if not set, a new :class:`.ResourceManager`
                is created

        Attributes:
            env (:class:`simpy.Environment`): Environment linked to this manager
            flow (DataFrame): Processes flow
            processes (dict_keys): All processes attached to this manager
            rm (:class:`.ResourceManager`): :class:`.ResourceManager` linked to this manager
        """
        super().__init__()
        self.env = kwargs.get('env', simpy.Environment())
        self.rm = kwargs.get('rm', ResourceManager(self.env))
        self.processes = self._store.keys()
        self.reset_flow()

    def create_resource(self, names, **kwargs):
        """
        Shortcut for `create_resource` method in :class:`.ResourceManager`.

        Args:
            names (str): List of names of resources to be created
            **kwargs: Arbitrary keyword arguments
        """
        self.rm.create_resource(names, **kwargs)

    def get_resource(self, name):
        """
        Shortcut for `get_resource` method in :class:`.ResourceManager`.

        Args:
            name (str): Name of the resource
        """
        return self.rm.get_resource(name)

    def get_resources(self, **kwargs):
        """
        Shortcut for `get_resources` method in :class:`.ResourceManager`.
        """
        return self.rm.get_resources(**kwargs)

    def attach_process(self, process_class, **kwargs):
        """
        Attach process to the simulation.

        Args:
            process_class (:class:`.Process`)

        Keyword Args:
            name (str): if not set, the name of the class is used
        """
        name = kwargs.get('name', process_class.__name__)
        process = process_class(self.env, self.rm, name)
        self._store[name] = process

    def get_process(self, name):
        """
        Get process by name.

        Args:
            name (str)

        Returns:
            :class:`.Process`
        """
        return self._store[name]

    def reset_flow(self):
        """
        Clear flow lookup table.
        """
        self.flow = DataFrame(columns=['from', 'to'])
        self.unblock_flow()

    def block_flow(self):
        """
        Prevents flow to be changed.
        """
        self.flow_blocked = True

    def unblock_flow(self):
        """
        Allows flow to be changed.
        """
        self.flow_blocked = False

    def set_flow(self, **kwargs):
        """
        Define the chain of processes.

        Keyword Args:
            initial_process (str): default initial process in the flow
            final_process (str): final process in the flow
            from_process (str): origin process in a specific pair of processes
            to_process (str): destination process in a specific pair of processes
            sequence (str): list of processes names in sequence, assuming the
                first/last as the initial_process/final_process
        """
        if self.flow_blocked:
            raise ValueError('Flow should not be changed after instantiating EventManger. \
                To force the definition of a new flow, call reset_flow.')

        if 'initial_process' in kwargs:
            self.flow = self.flow.append(
                {
                    'from': 'initial',
                    'to': kwargs['initial_process']
                },
                ignore_index=True
            )

        elif 'final_process' in kwargs:
            self.flow = self.flow.append(
                {
                    'from': kwargs['final_process'],
                    'to': 'final'
                },
                ignore_index=True
            )

        elif ('from_process' in kwargs) and ('to_process' in kwargs):
            self.flow = self.flow.append(
                {
                    'from': kwargs['from_process'],
                    'to': kwargs['to_process']
                },
                ignore_index=True
            )

        elif 'sequence' in kwargs:
            self.flow = self.flow.append(
                {
                    'from': 'initial',
                    'to': kwargs['sequence'][0]
                },
                ignore_index=True
            )
            for p in range(len(kwargs['sequence']) - 1):
                self.flow = self.flow.append(
                    {
                        'from': kwargs['sequence'][p],
                        'to': kwargs['sequence'][p + 1]
                    },
                    ignore_index=True
                )
            self.flow = self.flow.append(
                {
                    'from': kwargs['sequence'][-1],
                    'to': 'final'
                },
                ignore_index=True
            )
        else:
            warnings.warn(f'{kwargs} kwargs not recognised')
