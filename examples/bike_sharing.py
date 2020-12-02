import numpy as np
import random
from chronon import ProcessManager, EventManager, Process

STATIONS = ['Station A', 'Station B', 'Station C']
TARGET_OCCUPATION = 0.7
N_CYCLISTS = 7

pm = ProcessManager()

# Creating stations docks resources
docks = [random.randint(2, 4) for s in STATIONS]
for index, [name, capacity] in enumerate(zip(STATIONS, docks)):
    for d in range(capacity):
        pm.create_resource(f'dock_{index}{d}', type='dock', station=name)

# Defining distances between stations
station_x = np.array([round(random.uniform(0, 30), 2) for s in STATIONS])
distances = abs(station_x.reshape(-1, 1) - station_x)

# Bike processes
class IncludeBike(Process):
    def definition(self, bike):
        yield bike.waits(bike.initial_dock)


# Cyclist processes
class Cycle(Process):
    def get_bike_station(self, bike):
        dock = self.get_resources(by_user=bike.name)
        if len(dock) > 0:
            return dock[0].station
        else:
            return None

    def definition(self, cyclist):
        # Request a bike-resource
        cyclist.set_checkpoint(f'Requested a bike at {cyclist.from_station}')
        response = yield cyclist.waits(
            self.get_resources(by_properties={'type': 'bike'}),
            which='any'
        )

        # Get the bike-user by the name of the bike-resource obtained by the cyclist-user
        bike = cyclist.get_user(response.events[0].resource.name)

        # Undock bike-user from the station of origin
        origin_dock = self.get_resources(by_user=bike.name)[0]
        cyclist.set_checkpoint(f'Got {bike.name} at {origin_dock.station}')
        bike.releases(origin_dock)
        bike.set_checkpoint(f'Undocked from {origin_dock.name} at {origin_dock.station}')

        # Cycle to destination
        cycle_duration = distances[
            STATIONS.index(cyclist.from_station), 
            STATIONS.index(cyclist.to_station)
        ]
        yield bike.waits(cycle_duration)

        # Dock bike to the destination station
        bike.set_checkpoint(f'Requested a dock at {cyclist.to_station}')
        response = yield bike.waits(
            self.get_resources(by_properties={'type': 'dock'}),
            which='any'
        )
        dest_dock = response.events[0].resource
        bike.set_checkpoint(f'Docked on {dest_dock.name} at {dest_dock.station}')

        # Finish cycle
        cyclist.releases(self.get_resource(bike.name))
        cyclist.set_checkpoint(f'Left {bike.name} at {dest_dock.station}')

pm.attach_process(IncludeBike)
pm.attach_process(Cycle)
pm.set_flow(initial_process='IncludeBike')
pm.set_flow(final_process='IncludeBike')
pm.set_flow(initial_process='Cycle')
pm.set_flow(final_process='Cycle')

em = EventManager(pm)

# Creating bikes as resources (for customers) and users (of docks)
bid = 0
dock_resources = [d for d in pm.rm.resources]
for dock in dock_resources:
    if random.uniform(0, 1) < TARGET_OCCUPATION:
        pm.create_resource(
            f'bike_{bid}',
            type='bike'
        )
        em.create_user(
            f'bike_{bid}', 
            initial_process='IncludeBike',
            initial_dock=dock
        )
        bid += 1

# Creating cyclists
for c in range(N_CYCLISTS):
    from_station = random.choice(STATIONS)
    to_station = random.choice([s for s in STATIONS if s != from_station])
    em.create_user(
        f'cyclist_{c}',
        instant=round(random.uniform(0, 30), 2),
        initial_process='Cycle',
        from_station=from_station,
        to_station=to_station
    )
# em.create_user(
#     'cyclist', 
#     initial_process='Cycle',
#     from_station=random.choice(STATIONS),
#     to_station=random.choice(STATIONS)
# )

em.run()
for r in pm.rm.resources:
    print('\n', r)
    print(pm.get_resource(r).usage)

print(em.checkpoints)
