import openrouteservice
import pickle
import os
from itertools import combinations, permutations

client = openrouteservice.Client(key="5b3ce3597851110001cf6248b449f8b64be24fa4b2000df388c217c0")  # Ganti dengan API key kamu

restaurant = ("R", [107.63352405845339, -6.947680876741793])
customers = {
    "C1": [107.6550, -6.9480],
    "C2": [107.6150, -6.9400],
    "C3": [107.6250, -6.9600],
    "C4": [107.6450, -6.9300],
    "C5": [107.6100, -6.9500],
    "C6": [107.6400, -6.9700],
}
drivers = {
    "D1": [107.6250, -6.9400],
    "D2": [107.6200, -6.9700],
    "D3": [107.6400, -6.9550],
    "D4": [107.6500, -6.9450],
}

# === CACHE ===
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
        print(f"Error fetching duration from {coord1} to {coord2}: {e}")
        return float('inf')

# === BUILD RAW TRAVEL TIME TABLE ===
RAW_DATA = {}
for dname, dcoord in drivers.items():
    RAW_DATA[(dname, "R")] = get_duration(dcoord, restaurant[1]) / 60  

for cname, ccoord in customers.items():
    RAW_DATA[("R", cname)] = get_duration(restaurant[1], ccoord) / 60  

for cname1, ccoord1 in customers.items():
    for cname2, ccoord2 in customers.items():
        if cname1 != cname2:
            RAW_DATA[(cname1, cname2)] = get_duration(ccoord1, ccoord2) / 60  


driver_list = list(drivers.keys())
customer_list = list(customers.keys())
driver_to_rest = {d: RAW_DATA[(d, 'R')] for d in driver_list}
rest_to_cust = {c: RAW_DATA[('R', c)] for c in customer_list}
cust_to_cust = {(a, b): RAW_DATA[(a, b)] for a in customer_list for b in customer_list if a != b}

def tsp_cost(group):
    if not group:
        return 0
    best = float('inf')
    for route in permutations(group):
        cost = rest_to_cust[route[0]]
        for i in range(len(route) - 1):
            cost += cust_to_cust[(route[i], route[i+1])]
        best = min(best, cost)
    return best

def all_partitions(lst, k):
    if k == 1:
        yield [lst]
    else:
        for i in range(1, len(lst) - k + 2):
            for first in combinations(lst, i):
                rest = list(set(lst) - set(first))
                for others in all_partitions(rest, k - 1):
                    yield [list(first)] + others

def find_best_fair_assignment():
    best = None
    min_range = float('inf')

    for part in all_partitions(customer_list, 4):
        for d_perm in permutations(driver_list):
            times, assign = [], list(zip(d_perm, part))
            for d, group in assign:
                total = driver_to_rest[d] + tsp_cost(group)
                times.append(total)
            r = max(times) - min(times)
            if r < min_range:
                min_range = r
                best = {
                    'assignment': assign,
                    'times': [round(t, 2) for t in times],
                    'range': round(r, 2),
                    'mean': round(sum(times) / len(times), 2)
                }
    return best

def find_fastest_assignment():
    best = None
    min_total_time = float('inf')

    for part in all_partitions(customer_list, 4):
        for d_perm in permutations(driver_list):
            times, assign = [], list(zip(d_perm, part))
            for d, group in assign:
                total = driver_to_rest[d] + tsp_cost(group)
                times.append(total)
            total_time = sum(times)
            if total_time < min_total_time:
                min_total_time = total_time
                best = {
                    'assignment': assign,
                    'times': [round(t, 2) for t in times],
                    'total': round(total_time, 2),
                    'mean': round(total_time / len(times), 2),
                    'range': round(max(times) - min(times), 2)
                }
    return best

print("\n=== FAIRNESS-OPTIMIZED ASSIGNMENT ===")
fair_result = find_best_fair_assignment()
for (d, group), t in zip(fair_result['assignment'], fair_result['times']):
    print(f"{d} -> {group}, Total: {t} min")
print(f"\nMean Time: {fair_result['mean']} min")
print(f"Range (Fairness): {fair_result['range']} min")

print("\n=== FASTEST-TIME ASSIGNMENT ===")
fast_result = find_fastest_assignment()
for (d, group), t in zip(fast_result['assignment'], fast_result['times']):
    print(f"{d} -> {group}, Total: {t} min")
print(f"\nTotal Time: {fast_result['total']} min")
print(f"Mean Time: {fast_result['mean']} min")
print(f"Range (Fairness): {fast_result['range']} min")
