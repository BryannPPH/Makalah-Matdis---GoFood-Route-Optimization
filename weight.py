import openrouteservice

client = openrouteservice.Client(key="5b3ce3597851110001cf6248b449f8b64be24fa4b2000df388c217c0")

restaurant = ("Restaurant", [107.63352405845339, -6.947680876741793])

customers = {
    "Customer1": [107.6550, -6.9480],
    "Customer2": [107.6150, -6.9400],
    "Customer3": [107.6250, -6.9600],
    "Customer4": [107.6450, -6.9300],
    "Customer5": [107.6100, -6.9500],
    "Customer6": [107.6400, -6.9700],
}

drivers = {
    "Driver1": [107.6250, -6.9400],
    "Driver2": [107.6200, -6.9700],
    "Driver3": [107.6400, -6.9550],
    "Driver4": [107.6500, -6.9450],
}

import pickle
import os

cache_file = "duration_cache.pkl"
if os.path.exists(cache_file):
    with open(cache_file, "rb") as f:
        duration_cache = pickle.load(f)
else:
    duration_cache = {}

def get_duration(coord1, coord2):
    key = tuple(sorted((tuple(coord1), tuple(coord2))))
    if key in duration_cache:
        return duration_cache[key]
    try:
        res = client.directions([coord1, coord2], profile='driving-car')
        duration = res['routes'][0]['summary']['duration']
        duration_cache[key] = duration
        with open(cache_file, "wb") as f:
            pickle.dump(duration_cache, f)
        return duration
    except Exception as e:
        print(f"Error fetching {coord1} to {coord2}: {e}")
        return float('inf')

print("\nTABLE 1: Time from Driver to Restaurant\n")
print("{:<10} {:>20}".format("Driver", "Time (minutes)"))
print("-" * 32)
for dname, dcoord in drivers.items():
    time = get_duration(dcoord, restaurant[1]) / 60  
    print("{:<10} {:>14.2f} min".format(dname, time))

print("\nTABLE 2: Time from Restaurant to Customer\n")
print("{:<12} {:>20}".format("Customer", "Time (minutes)"))
print("-" * 34)
for cname, ccoord in customers.items():
    time = get_duration(restaurant[1], ccoord) / 60
    print("{:<12} {:>14.2f} min".format(cname, time))

print("\nTABLE 3: Time from Customer to Customer\n")

short_names = {f"Customer{i+1}": f"C{i+1}" for i in range(len(customers))}

header = ["From\\To"] + list(short_names.values())
print("{:<8}".format(header[0]), end="")
for name in header[1:]:
    print("{:>8}".format(name), end="")
print()
print("-" * (8 * len(header)))

for cname1, ccoord1 in customers.items():
    short1 = short_names[cname1]
    print("{:<8}".format(short1), end="")
    for cname2, ccoord2 in customers.items():
        if cname1 == cname2:
            print("{:>8}".format("—"), end="")  
        else:
            time = get_duration(ccoord1, ccoord2) / 60
            print("{:>8.2f}".format(time), end="")
    print()

