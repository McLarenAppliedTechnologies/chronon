import random
from chronon import ProcessManager, EventManager, Process


# RANDOM_SEED = 42
NEW_CUSTOMERS = 7  # Total number of customers
NUMBER_OF_COUNTERS = 1 # Total number of counters
INTERVAL_CUSTOMERS = 3.0  # Generate new customers roughly every x seconds
MIN_PATIENCE = 1  # Min. customer patience
MAX_PATIENCE = 5  # Max. customer patience


# create process manager
pm = ProcessManager()

# create resource
pm.create_resource('counters', capacity=NUMBER_OF_COUNTERS)

# process definition
class CustomerWaitCounter(Process):
    def definition(self, user):
        # time when customer arrives
        arrive = self.env.now
        user.set_checkpoint('Arrived')
        # amount of patience a customer can have
        patience = random.uniform(MIN_PATIENCE, MAX_PATIENCE)
        # waiting...
        yield user.waits('counters', patience=patience)
        # calculate time waited since customer arrived
        wait = self.env.now - arrive
        if wait < patience:
            # clients go to the counter
            user.set_checkpoint(f'Got to the counter')
            time_discussing = 12.0
            td = random.expovariate(1.0 / time_discussing)
            # yield as long as the customer is discussing at the counter
            yield user.waits(td)
            # release the resource
            user.releases('counters')
            user.set_checkpoint('Finished')
        else:
            # release the resource
            user.releases('counters')
            # customer reneged
            user.set_checkpoint('Reneged')


# store process into process Manager
pm.attach_process(CustomerWaitCounter)

# create event manager
em = EventManager(pm)
for i in range(NEW_CUSTOMERS):
    # create new customer
    t = random.expovariate(1.0 / INTERVAL_CUSTOMERS)
    em.create_user(f'Customer {i}', instant=t)

# random.seed(RANDOM_SEED)

if __name__ == '__main__':
    # execute the program
    em.run()
    print(em.checkpoints)
    print(pm.get_resource('counters').usage)
