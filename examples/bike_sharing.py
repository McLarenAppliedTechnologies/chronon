import numpy as np
import random
from chronon import ProcessManager, EventManager, Process, Resource

STATIONS = ['Station A', 'Station B', 'Station C']
TARGET_OCCUPATION = 0.7
N_CYCLISTS = 7

pm = ProcessManager()

# Defining distances between stations
station_x = np.array([round(random.uniform(0, 30), 2) for s in STATIONS])
distances = abs(station_x.reshape(-1, 1) - station_x)

# Bike process
class IncludeBike(Process):
    def definition(self, bike):
        yield bike.waits(bike.initial_dock)

# Cyclist process
class Cycle(Process):
    def definition(self, cyclist):
        # Request a bike-as-resource
        cyclist.set_checkpoint(f'Requested a bike at {cyclist.from_station}')
        response = yield cyclist.waits(
            self.get_resources(by_properties={'type': 'bike'}),
            which='any',
            having={'station': cyclist.from_station}
        )

        # Get the bike-as-user based on the name of the bike-as-resource obtained by the cyclist-as-user
        bike_resource = response.events[0].resource
        bike = cyclist.get_user(bike_resource.name)

        # Undock bike-as-user from the station of origin
        origin_dock = self.get_resources(by_user=bike)[0]
        cyclist.set_checkpoint(
            f'Got {bike_resource.name} at {origin_dock.station}'
        )
        bike.releases(origin_dock)
        bike.set_checkpoint(
            f'Undocked from {origin_dock.name} at {origin_dock.station}'
        )

        # Cycle to destination
        cycle_duration = distances[
            STATIONS.index(cyclist.from_station), 
            STATIONS.index(cyclist.to_station)
        ]
        bike.set_checkpoint(f'Moving')
        yield bike.waits(cycle_duration)

        # Dock bike-as-user at the destination station
        bike.set_checkpoint(f'Requested a dock at {cyclist.to_station}')
        response = yield bike.waits(
            self.get_resources(by_properties={
                'type': 'dock', 
                'station': cyclist.to_station
            }),
            which='any',
        )
        dest_dock = response.events[0].resource
        bike.set_checkpoint(f'Docked on {dest_dock.name} at {dest_dock.station}')

        # Finish cycle
        cyclist.releases(bike_resource)
        cyclist.set_checkpoint(
            f'Left {bike_resource.name} at {dest_dock.station}'
        )

pm.attach_process(IncludeBike)
pm.attach_process(Cycle)
pm.set_flow(initial_process='IncludeBike')
pm.set_flow(final_process='IncludeBike')
pm.set_flow(initial_process='Cycle')
pm.set_flow(final_process='Cycle')

em = EventManager(pm)

# Custom Resource class for bikes
class BikeResource(Resource):
    @property
    def station(self):
        # Bike-user and bike-resource have the same name
        dock = self.rm.get_resources(by_user=self.name)
        if len(dock) == 0:
            return None
        else:
            return dock[0].station

# Creating station docks as resources
docks = [random.randint(2, 4) for s in STATIONS]
for index, [name, capacity] in enumerate(zip(STATIONS, docks)):
    for d in range(capacity):
        pm.create_resource(f'dock_{index}{d}', type='dock', station=name)

# Creating bikes as resources (for customers) and users (of docks)
bid = 0
dock_resources = pm.get_resources(by_properties={'type': 'dock'})
for dock in dock_resources:
    if random.uniform(0, 1) < TARGET_OCCUPATION:
        pm.create_resource(
            f'bike_{bid}',
            custom_resource=BikeResource,
            type='bike'
        )
        em.create_user(
            f'bike_{bid}',
            initial_process='IncludeBike',
            initial_dock=dock
        )
        bid += 1

# Creating cyclists as users
for c in range(N_CYCLISTS):
    from_station = random.choice(STATIONS)
    to_station = random.choice([s for s in STATIONS if s != from_station])
    user = em.create_user(
        f'cyclist_{c}',
        instant=round(random.uniform(0, 30), 2),
        initial_process='Cycle',
        from_station=from_station,
        to_station=to_station
    )

# Running simulation
em.run()

# Reporting
for r in pm.rm.resources:
    print('\n', r)
    print(pm.get_resource(r).usage)

print(em.checkpoints)
