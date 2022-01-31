# UiB INF273-Meta-Heuristikkar Pickup and Delivery Problem utils
This Repo is dedicated to the function utils needed for the course project semester spring 2022.

# Requirement
- numpy

## Usage
### 1) You can install the library by typing the following in terminal:
```bash
python setup.py install
```
### 2) You can load the problem instance using the following line

```bash
from pdp_utils import load_problem

prob = load_problem(*PROBLEM_FILE_ADDRESS*)
```
The function returns dictionary that includes the following information about each problem instance:
- **'n_nodes'**: _number of nodes_
- **'n_vehicles':** _number of vehicles_ 
- **'n_calls':** _number of calls_ 
- **'cargo':** _information about each call_
- **'travel_time'**: _for each vehicle the travel time from one node to another_
- **'first_travel_time'**: _for each vehicle the travel time from starting point to each node_ 
- **'vessel_capacity'**: _the capacity of each vehicle_
- **'loading_time'**: _for each vehicle the loading time of pickup of each call (-1 indicates not allowed)_ 
- **'unloading_time'**: _for each vehicle the un-loading time of pickup of each call (-1 indicates not allowed)_ 
- **'vessel_cargo'**: _the list of allowed calls for each vehicle_
- **'travel_cost'**: _for each vehicle the travel cost from one node to another_
- **'first_travel_cost'**:  _for each vehicle the travel cost from starting point to each node_
- **'port_cost'**: _the cost of answering a call for each vehicle (-2 indicates not allowed)_
### 3) You can check the feasiblity of your asnwer like below:
```bash
from pdp_utils import feasibility_check

feasible, log = feasibility_check(SOL, prob)

print(log)
```
### 4) You can check the cost function of a sulotion as below:
```bash
from pdp_utils import cost_function

cost = cost_function(SOL, prob)
```