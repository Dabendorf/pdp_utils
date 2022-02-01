import numpy as np
from collections import namedtuple


def load_problem(filename: str):
	"""
	Function which reads an input file into a datastructure

	:param filename: Address of the problem input file
	:return: Named tuple object of problem attributes
	"""
	temp_vehicle_info = []
	temp_vehicle_call_list = []
	temp_call_info = []
	temp_travel_times = []
	temp_node_costs = []

	# Reading the file
	with open(filename) as f:
		# Read 1: number of nodes
		line = f.readline().strip()
		if not line.startswith("%"):
			raise ValueError("Missing comment line 'number of nodes'")
		num_nodes = int(f.readline().strip())

		# Read 2: number of vehicles
		line = f.readline().strip()
		if not line.startswith("%"):
			raise ValueError("Missing comment line 'number of vehicles'")
		num_vehicles = int(f.readline().strip())

		# Read 3: for each vehicle: idx, home node, starting time, capacity (4 columns)
		line = f.readline().strip()
		if not line.startswith("%"):
			raise ValueError("Missing comment line 'for each vehicles (time, capacity)'")
		for i in range(num_vehicles):
			temp_vehicle_info.append(f.readline().strip().split(","))

		# Read 4: number of calls
		line = f.readline().strip()
		if not line.startswith("%"):
			raise ValueError("Missing comment line 'number of calls'")
		num_calls = int(f.readline().strip())

		# Read 5: for each vehicle: idx, [list of possible calls] (2 columns)
		line = f.readline().strip()
		if not line.startswith("%"):
			raise ValueError("Missing comment line 'for each vehicles (list of transportable calls)'")
		for i in range(num_vehicles):
			temp_vehicle_call_list.append(f.readline().strip().split(","))

		# Read 6: for each call: idx, origin_node, dest_node, size, ... (9 columns)
		line = f.readline().strip()
		if not line.startswith("%"):
			raise ValueError("Missing comment line 'for each call'")
		for i in range(num_calls):
			temp_call_info.append(f.readline().strip().split(","))
		
		# Read 7: travel times and costs (5 columns)
		line = f.readline().strip()
		if not line.startswith("%"):
			raise ValueError("Missing comment line 'travel times and costs'")

		line = f.readline()
		while not line.startswith("%"):
			temp_travel_times.append(line.strip().split(","))
			line = f.readline()

		# Read 8: node times and costs (6 columns), read until EOF
		if not line.startswith("%"):
			raise ValueError("Missing comment line 'node times and costs'")
		line = f.readline()
		while not line.startswith("%"):
			temp_node_costs.append(line.strip().split(","))
			line = f.readline()

	cargo = np.array(temp_call_info, dtype=np.double)[:, 1:]
	temp_travel_times = np.array(temp_travel_times, dtype=np.int)

	travel_time = np.zeros((num_vehicles + 1, num_nodes + 1, num_nodes + 1))
	travel_cost = np.zeros((num_vehicles + 1, num_nodes + 1, num_nodes + 1))
	for j in range(len(temp_travel_times)):
		travel_time[temp_travel_times[j, 0]][temp_travel_times[j, 1], temp_travel_times[j, 2]] = temp_travel_times[j, 3]
		travel_cost[temp_travel_times[j, 0]][temp_travel_times[j, 1], temp_travel_times[j, 2]] = temp_travel_times[j, 4]

	vessel_capacity = np.zeros(num_vehicles)
	starting_time = np.zeros(num_vehicles)
	first_travel_time = np.zeros((num_vehicles, num_nodes))
	first_travel_cost = np.zeros((num_vehicles, num_nodes))
	temp_vehicle_info = np.array(temp_vehicle_info, dtype=np.int)
	for i in range(num_vehicles):
		vessel_capacity[i] = temp_vehicle_info[i, 3]
		starting_time[i] = temp_vehicle_info[i, 2]
		for j in range(num_nodes):
			first_travel_time[i, j] = travel_time[i + 1, temp_vehicle_info[i, 1], j + 1] + temp_vehicle_info[i, 2]
			first_travel_cost[i, j] = travel_cost[i + 1, temp_vehicle_info[i, 1], j + 1]
	travel_time = travel_time[1:, 1:, 1:]
	travel_cost = travel_cost[1:, 1:, 1:]
	vessel_cargo = np.zeros((num_vehicles, num_calls + 1))
	temp_vehicle_call_list = np.array(temp_vehicle_call_list, dtype=object)
	for i in range(num_vehicles):
		vessel_cargo[i, np.array(temp_vehicle_call_list[i][1:], dtype=np.int)] = 1
	vessel_cargo = vessel_cargo[:, 1:]

	loading_time = np.zeros((num_vehicles + 1, num_calls + 1))
	unloading_time = np.zeros((num_vehicles + 1, num_calls + 1))
	port_cost = np.zeros((num_vehicles + 1, num_calls + 1))
	temp_node_costs = np.array(temp_node_costs, dtype=np.int)
	for i in range(num_vehicles * num_calls):
		loading_time[temp_node_costs[i, 0], temp_node_costs[i, 1]] = temp_node_costs[i, 2]
		unloading_time[temp_node_costs[i, 0], temp_node_costs[i, 1]] = temp_node_costs[i, 4]
		port_cost[temp_node_costs[i, 0], temp_node_costs[i, 1]] = temp_node_costs[i, 5] + temp_node_costs[i, 3]

	loading_time = loading_time[1:, 1:]
	unloading_time = unloading_time[1:, 1:]
	port_cost = port_cost[1:, 1:]
	output = {
		'n_nodes': num_nodes,
		'n_vehicles': num_vehicles,
		'n_calls': num_calls,
		'cargo': cargo,
		'travel_time': travel_time,
		'first_travel_time': first_travel_time,
		'vessel_capacity': vessel_capacity,
		'loading_time': loading_time,
		'unloading_time': unloading_time,
		'vessel_cargo': vessel_cargo,
		'travel_cost': travel_cost,
		'first_travel_cost': first_travel_cost,
		'port_cost': port_cost
	}
	return output


def feasibility_check(solution, problem):
	"""

	:rtype: tuple
	:param solution: The input solution of order of calls for each vehicle to the problem
	:param problem: The pickup and delivery problem object
	:return: whether the problem is feasible and the reason for probable infeasibility
	"""
	num_vehicles = problem['n_vehicles']
	cargo = problem['cargo']
	travel_time = problem['travel_time']
	first_travel_time = problem['first_travel_time']
	vessel_capacity = problem['vessel_capacity']
	loading_time = problem['loading_time']
	unloading_time = problem['unloading_time']
	vessel_cargo = problem['vessel_cargo']

	solution = np.append(solution, [0])
	zero_index = np.array(np.where(solution == 0)[0], dtype=int)
	feasibility = True
	tempidx = 0
	c = 'Feasible'
	for i in range(num_vehicles):
		currentVPlan = solution[tempidx:zero_index[i]]
		currentVPlan = currentVPlan - 1
		no_double_call_on_vehicle = len(currentVPlan)
		tempidx = zero_index[i] + 1
		if no_double_call_on_vehicle > 0:

			if not np.all(vessel_cargo[i, currentVPlan]):
				feasibility = False
				c = 'incompatible vessel and cargo'
				break
			else:
				load_size = 0
				current_time = 0
				sortRout = np.sort(currentVPlan, kind='mergesort')
				I = np.argsort(currentVPlan, kind='mergesort')
				indx = np.argsort(I, kind='mergesort')
				load_size -= cargo[sortRout, 2]
				load_size[::2] = cargo[sortRout[::2], 2]
				load_size = load_size[indx]
				if np.any(vessel_capacity[i] - np.cumsum(load_size) < 0):
					feasibility = False
					c = 'Capacity exceeded'
					break
				time_windows = np.zeros((2, no_double_call_on_vehicle))
				time_windows[0] = cargo[sortRout, 6]
				time_windows[0, ::2] = cargo[sortRout[::2], 4]
				time_windows[1] = cargo[sortRout, 7]
				time_windows[1, ::2] = cargo[sortRout[::2], 5]

				time_windows = time_windows[:, indx]

				port_index = cargo[sortRout, 1].astype(int)
				port_index[::2] = cargo[sortRout[::2], 0]
				port_index = port_index[indx] - 1

				lu_time = unloading_time[i, sortRout]
				lu_time[::2] = loading_time[i, sortRout[::2]]
				lu_time = lu_time[indx]
				diag = travel_time[i, port_index[:-1], port_index[1:]]
				first_visit_time = first_travel_time[i, int(
					cargo[currentVPlan[0], 0] - 1)]

				route_travel_time = np.hstack((first_visit_time, diag.flatten()))

				arrive_time = np.zeros(no_double_call_on_vehicle)
				for j in range(no_double_call_on_vehicle):
					arrive_time[j] = np.max(
						(current_time + route_travel_time[j], time_windows[0, j]))
					if arrive_time[j] > time_windows[1, j]:
						feasibility = False
						c = 'Time window exceeded at call {}'.format(j)
						break
					current_time = arrive_time[j] + lu_time[j]

	return feasibility, c


def cost_function(solution, problem):
	"""

	:param solution: the proposed solution for the order of calls in each vehicle
	:param problem:
	:return:
	"""

	num_vehicles = problem['n_vehicles']
	cargo = problem['cargo']
	travel_cost = problem['travel_cost']
	first_travel_cost = problem['first_travel_cost']
	port_cost = problem['port_cost']

	not_transport_cost = 0
	route_travel_cost = np.zeros(num_vehicles)
	cost_in_ports = np.zeros(num_vehicles)

	solution = np.append(solution, [0])
	zero_index = np.array(np.where(solution == 0)[0], dtype=int)
	tempidx = 0

	for i in range(num_vehicles + 1):
		currentVPlan = solution[tempidx:zero_index[i]]
		currentVPlan = currentVPlan - 1
		no_double_call_on_vehicle = len(currentVPlan)
		tempidx = zero_index[i] + 1

		if i == num_vehicles:
			not_transport_cost = np.sum(cargo[currentVPlan, 3]) / 2
		else:
			if no_double_call_on_vehicle > 0:
				sortRout = np.sort(currentVPlan, kind='mergesort')
				I = np.argsort(currentVPlan, kind='mergesort')
				indx = np.argsort(I, kind='mergesort')

				port_index = cargo[sortRout, 1].astype(int)
				port_index[::2] = cargo[sortRout[::2], 0]
				port_index = port_index[indx] - 1

				diag = travel_cost[i, port_index[:-1], port_index[1:]]

				first_visit_cost = first_travel_cost[i, int(
					cargo[currentVPlan[0], 0] - 1)]
				route_travel_cost[i] = np.sum(
					np.hstack((first_visit_cost, diag.flatten())))
				cost_in_ports[i] = np.sum(port_cost[i, currentVPlan]) / 2

	total_cost = not_transport_cost + \
		sum(route_travel_cost) + sum(cost_in_ports)
	return total_cost
