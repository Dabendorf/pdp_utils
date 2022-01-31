import numpy as np
from collections import namedtuple


def load_problem(filename):
    """

    :rtype: object
    :param filename: The address to the problem input file
    :return: named tuple object of the problem attributes
    """
    A = []
    B = []
    C = []
    D = []
    E = []
    with open(filename) as f:
        lines = f.readlines()
        num_nodes = int(lines[1])
        num_vehicles = int(lines[3])
        num_calls = int(lines[num_vehicles + 5 + 1])

        for i in range(num_vehicles):
            A.append(lines[1 + 4 + i].split(','))

        for i in range(num_vehicles):
            B.append(lines[1 + 7 + num_vehicles + i].split(','))

        for i in range(num_calls):
            C.append(lines[1 + 8 + num_vehicles * 2 + i].split(','))

        for j in range(num_nodes * num_nodes * num_vehicles):
            D.append(lines[1 + 2 * num_vehicles +
                     num_calls + 9 + j].split(','))

        for i in range(num_vehicles * num_calls):
            E.append(lines[1 + 1 + 2 * num_vehicles +
                     num_calls + 10 + j + i].split(','))
        f.close()

    cargo = np.array(C, dtype=np.double)[:, 1:]
    D = np.array(D, dtype=np.int)

    travel_time = np.zeros((num_vehicles + 1, num_nodes + 1, num_nodes + 1))
    travel_cost = np.zeros((num_vehicles + 1, num_nodes + 1, num_nodes + 1))
    for j in range(len(D)):
        travel_time[D[j, 0]][D[j, 1], D[j, 2]] = D[j, 3]
        travel_cost[D[j, 0]][D[j, 1], D[j, 2]] = D[j, 4]

    vessel_capacity = np.zeros(num_vehicles)
    starting_time = np.zeros(num_vehicles)
    first_travel_time = np.zeros((num_vehicles, num_nodes))
    first_travel_cost = np.zeros((num_vehicles, num_nodes))
    A = np.array(A, dtype=np.int)
    for i in range(num_vehicles):
        vessel_capacity[i] = A[i, 3]
        starting_time[i] = A[i, 2]
        for j in range(num_nodes):
            first_travel_time[i, j] = travel_time[i + 1, A[i, 1], j + 1] + A[i, 2]
            first_travel_cost[i, j] = travel_cost[i + 1, A[i, 1], j + 1]
    travel_time = travel_time[1:, 1:, 1:]
    travel_cost = travel_cost[1:, 1:, 1:]
    vessel_cargo = np.zeros((num_vehicles, num_calls + 1))
    B = np.array(B, dtype=object)
    for i in range(num_vehicles):
        vessel_cargo[i, np.array(B[i][1:], dtype=np.int)] = 1
    vessel_cargo = vessel_cargo[:, 1:]

    loading_time = np.zeros((num_vehicles + 1, num_calls + 1))
    unloading_time = np.zeros((num_vehicles + 1, num_calls + 1))
    port_cost = np.zeros((num_vehicles + 1, num_calls + 1))
    E = np.array(E, dtype=np.int)
    for i in range(num_vehicles * num_calls):
        loading_time[E[i, 0], E[i, 1]] = E[i, 2]
        unloading_time[E[i, 0], E[i, 1]] = E[i, 4]
        port_cost[E[i, 0], E[i, 1]] = E[i, 5] + E[i, 3]

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
