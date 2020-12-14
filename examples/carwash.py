import numpy as np
import random
from datetime import timedelta, datetime
from chronon import ProcessManager, EventManager, Process


RANDOM_SEED = 42
NUM_MACHINES = 2  # Number of machines in the carwash
WASHTIME = 5      # Minutes it takes to clean a car
T_INTER = 3       # Create a car every ~T_INTER minutes
SIM_TIME = 25     # Simulation time in minutes
N_INITIAL = 1     # Number of cars in the car wash at the start


# Instantiate Process Manager
random.seed(RANDOM_SEED)
pm = ProcessManager()

# Create car wash with NUM_MACHINE machines and attach car wash process
pm.create_resource('machines', capacity=NUM_MACHINES)


class CarWash(Process):
    def definition(self, user):
        # Car arrives and requests the use of a machine
        yield user.waits('machines')

        # Car enters the car wash and spends WASHTIME minutes inside
        yield user.waits(timedelta(minutes=WASHTIME))

        # Car leaves the car wash and releases the machine for the next car to use
        user.set_checkpoint(f'Left the carwash. {random.randint(50, 99)}% of dirt removed.')
        user.releases('machines')

pm.attach_process(CarWash)

# Create event stream
em = EventManager(pm)
now = datetime.now()
times = np.concatenate([np.zeros(3), np.random.randint(T_INTER-2, T_INTER+2, int(SIM_TIME/(T_INTER-2)))]).cumsum()
for i, t in enumerate(times):
    em.create_user(f'Car {i}', instant=now+timedelta(minutes=t))

if __name__ == '__main__':
    # Execute!
    em.run(until=now+timedelta(minutes=SIM_TIME))
    print(em.checkpoints)
    print(pm.get_resource('machines').usage)
