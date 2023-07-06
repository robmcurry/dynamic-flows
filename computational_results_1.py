# -*- coding: utf-8 -*-
"""(A7) Computational Results 1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1QXTLNAv70ZYrP2tWr2JFjav4WG88Fnfp
"""

import pyomo.environ as pyo
import pandas as pd
import numpy as np
import xlrd
import xlwt
import xlsxwriter
import xlwings as xw
import random
import time
import math

master = {}
scenarios = []
tests = []

for i in range(1,14):
    scenarios.append(i)
for i in range(1,6):
    tests.append(i)


# scenario: (nodes, time periods, density, budget)
master = {1: (20,50,.5,100),
         2: (10,50,.5,100),
         3: (25,50,.5,100),
         4: (20,40,.5,100),
         5: (20,60,.5,100),
         6: (20,70,.5,100),
         7: (20,50,.25,100),
         8: (20,50,.75,100),
         9: (20,50,1,100),
         10: (20,50,'lexical',100),
         11: (20,50,.5,50),
         12: (20,50,.5,150),
         13: (20,50,.5,200),
         14: (20,50,.5,100)}

# total amount of assets
f = 100

def build_model1(V, V1, A, T, T2, b, l, v, c, m, B):

    start_time = time.time()

    # Model creation with all constraints, decision variables, and objective function
    model = pyo.ConcreteModel()
    # number of assets sent on arc i,j during t
    model.x = pyo.Var(A, T, domain=pyo.NonNegativeIntegers)
    # number of assets starting at i during t
    model.w = pyo.Var(V, T2, domain=pyo.NonNegativeIntegers)
    # 1 if x[i,j,t] >= l[i,t] at i during t, 0 o.w.
    model.z = pyo.Var(V, T, domain=pyo.Binary)


    def obj_rule(model):
        return sum(model.z[i,t]*v[i,t] for i in V1 for t in T)
    model.obj = pyo.Objective(rule = obj_rule, sense = pyo.maximize)

    def flow_balance_rule(model, i, t):
        return sum(model.x[j,i,t] for j in V if (j,i) in A) - sum(model.x[i,j,t] for j in V if (i,j) in A) + model.w[i,t-1] == model.w[i,t]
    model.flow_balance_constraint = pyo.Constraint(V, T, rule=flow_balance_rule)

    def value_rule(model, i, t):
        return model.w[i,t] >= l[i,t]*model.z[i,t]
    model.value_constraint = pyo.Constraint(V1, T,rule=value_rule)

    def capacity_rule(model, i, t):
        return model.w[i,t] <= m[i,t]
    model.capacity_constraint = pyo.Constraint(V1, T, rule=capacity_rule)

    def starting_value_rule(model, i):
        return model.w[i,0] == b[i]
    model.starting_value_constraint = pyo.Constraint(V, rule=starting_value_rule)

    def budget_rule(model, t):
        return sum(model.x[i,j,t]*c[(i,j),t] for (i,j) in A) <= B[t]
    model.budget_constraint = pyo.Constraint(T, rule=budget_rule)




    solver = pyo.SolverFactory('gurobi')
    solver.options['TimeLimit'] = 1800

    solver_result = solver.solve(model)

    runtime = time.time() - start_time


    # objective function value
    total_value = sum(model.z[i,t].value*v[i,t] for i in V1 for t in T)

    return total_value, runtime

def build_model3(V, V1, A, first, last, b, l, v, c, m, B):

    #Create time periods
    T = []
    T2 = [first-1]
    for q in range(first,last+1):
        T.append(q)
        T2.append(q)

    start_time = time.time()

    # Model creation with all constraints, decision variables, and objective function
    model = pyo.ConcreteModel()
    # number of assets sent on arc i,j during t
    model.x = pyo.Var(A, T, domain=pyo.NonNegativeIntegers)
    # number of assets starting at i during t
    model.w = pyo.Var(V, T2, domain=pyo.NonNegativeIntegers)
    # 1 if x[i,j,t] >= l[i,t] at i during t, 0 o.w.
    model.z = pyo.Var(V, T, domain=pyo.Binary)


    def obj_rule(model):
        return sum(model.z[i,t]*v[i,t] for i in V1 for t in T)
    model.obj = pyo.Objective(rule = obj_rule, sense = pyo.maximize)

    def flow_balance_rule(model, i, t):
        return sum(model.x[j,i,t] for j in V if (j,i) in A) - sum(model.x[i,j,t] for j in V if (i,j) in A) + model.w[i,t-1] == model.w[i,t]
    model.flow_balance_constraint = pyo.Constraint(V, T, rule=flow_balance_rule)

    def value_rule(model, i, t):
        return model.w[i,t] >= l[i,t]*model.z[i,t]
    model.value_constraint = pyo.Constraint(V1, T, rule=value_rule)

    def capacity_rule(model, i, t):
        return model.w[i,t] <= m[i,t]
    model.capacity_constraint = pyo.Constraint(V1, T, rule=capacity_rule)

    def starting_value_rule(model, i):
        return model.w[i,first-1] == b[i]
    model.starting_value_constraint = pyo.Constraint(V, rule=starting_value_rule)

    def budget_rule(model, t):
        return sum(model.x[i,j,t]*c[(i,j),t] for (i,j) in A) <= B[t]
    model.budget_constraint = pyo.Constraint(T, rule=budget_rule)

    solver = pyo.SolverFactory('gurobi')
    solver.options['TimeLimit'] = 300

    solver_result = solver.solve(model)

    runtime = time.time() - start_time

    flows = {}
    total_value = 0
    for i in V:
        flows[i] = model.w[i,last].value

    total_value = sum(model.z[i,t].value*v[i,t] for i in V1 for t in T)

    return flows, total_value, runtime

begin = time.time()

book = xlwt.Workbook()
sht = book.add_sheet("Results")

sht.write(0,0,'scenario')
sht.write(0,1,'test')
sht.write(0,2,'Model 1 Value')
sht.write(0,3,'Model 1 Time')
sht.write(0,4,'Model 3 Value')
sht.write(0,5,'Model 3 Time')

k = 1

book.save(f"Computational Results 2.xls")



for scenario in [7,8,9,10,11,12,13]:
    for test in tests:

        (num_nodes, num_time_periods, density, budget) = master[scenario]



        # Sets
        V = [0]
        V1 = []
        T = []
        T2 = [0]
        A = []

        # Create Excel sheet data types in Python
        Excel_name = f"ParameterData_S{scenario}_T{test}.xls"

        wb = xw.Book(Excel_name)
        shtl = wb.sheets('Lower Bound')
        shtv = wb.sheets('Value')
        shtc = wb.sheets('Cost')
        shtm = wb.sheets('Max Capacity')
        shtB = wb.sheets('Budget')

        # Sets
        V1 = shtl.range('A2').expand('down').value
        for i in V1:
            V.append(i)
        T = shtl.range('B1').expand('right').value
        for t in T:
            T2.append(t)
        Arcs = shtc.range('A2').expand('down').value

        for i in Arcs:
            i = i.strip('(').strip(')')
            tupl = tuple(map(int, i.split(',')))
            A.append(tupl)


        # Parameter matrices pulled from excel spreadsheet
        wb = pd.read_excel(Excel_name)

        lower_bound = pd.read_excel(Excel_name, sheet_name= 'Lower Bound')
        value = pd.read_excel(Excel_name, sheet_name= 'Value')
        cost = pd.read_excel(Excel_name, sheet_name= 'Cost')
        max_capacity = pd.read_excel(Excel_name, sheet_name= 'Max Capacity')
        budget = pd.read_excel(Excel_name, sheet_name= 'Budget')

        #Paramter Dictionary
        l = {}
        for i in range(len(V1)):
            for j in range(len(T)):
                l[(V1[i], T[j])] = lower_bound.iloc[i,j+1]

        v = {}
        for i in range(len(V1)):
            for j in range(len(T)):
                v[(V1[i], T[j])] = value.iloc[i,j+1]

        c = {}
        for i in range(len(A)):
            for j in range(len(T)):
                c[(A[i], T[j])] = cost.iloc[i,j+1]

        m = {}
        for i in range(len(V1)):
            for j in range(len(T)):
                m[(V1[i], T[j])] = max_capacity.iloc[i,j+1]


        B = {}
        for i in range(len(T)):
                B[T[i]] = lower_bound.iloc[1,i+1]




        print(f'Scenario {scenario} and Test {test}:')


        #Model1
        b = {0: f}
        for i in V1:
            b[i] = 0

        objective_value, model1_time = build_model1(V, V1, A, T, T2, b, l, v, c, m, B)

        print(f'Model 1: Value = {objective_value}, Time = {model1_time} seconds')
        print(time.time() - begin)

        sht.write(k,0,scenario)
        sht.write(k,1,test)
        sht.write(k,2,objective_value)
        sht.write(k,3,model1_time)


        #Reset b
        b = {0: f}
        for i in V1:
            b[i] = 0


        #Hueristic Model3
        step_size = 10
        first = 1
        last = first + step_size - 1
        total_objective = 0
        model3_time = 0

        while last <= num_time_periods:
            b, objective, runtime = build_model3(V, V1, A, first, last, b, l, v, c, m, B)
            first += step_size
            last = first + step_size - 1
            total_objective += objective
            model3_time += runtime

        print(f'Model 3: Value = {total_objective}, Time = {model3_time} seconds')
        print(time.time() - begin)


        sht.write(k,4,total_objective)
        sht.write(k,5,model3_time)


        k += 1

        book.save(f"Computational Results 2.xls")

begin = time.time()

book = xlwt.Workbook()
sht = book.add_sheet("Results")

sht.write(0,0,'(scenario, test)')
sht.write(0,1,'Model 1 Value')
sht.write(0,2,'Model 1 Time')
sht.write(0,3,'Model 3 Value')
sht.write(0,4,'Model 3 Time')


book.save(f"Computational Results S3.xls")

k = 1

scenario = 3
for test in tests:


    (num_nodes, num_time_periods, density, budget) = master[scenario]



    # Sets
    V = [0]
    V1 = []
    T = []
    T2 = [0]
    A = []

    # Create Excel sheet data types in Python
    Excel_name = f"ParameterData_S{scenario}_T{test}.xls"

    wb = xw.Book(Excel_name)
    shtl = wb.sheets('Lower Bound')
    shtv = wb.sheets('Value')
    shtc = wb.sheets('Cost')
    shtm = wb.sheets('Max Capacity')
    shtB = wb.sheets('Budget')

    # Sets
    V1 = shtl.range('A2').expand('down').value
    for i in V1:
        V.append(i)
    T = shtl.range('B1').expand('right').value
    for t in T:
        T2.append(t)
    Arcs = shtc.range('A2').expand('down').value

    for i in Arcs:
        i = i.strip('(').strip(')')
        tupl = tuple(map(int, i.split(',')))
        A.append(tupl)


    # Parameter matrices pulled from excel spreadsheet
    wb = pd.read_excel(Excel_name)

    lower_bound = pd.read_excel(Excel_name, sheet_name= 'Lower Bound')
    value = pd.read_excel(Excel_name, sheet_name= 'Value')
    cost = pd.read_excel(Excel_name, sheet_name= 'Cost')
    max_capacity = pd.read_excel(Excel_name, sheet_name= 'Max Capacity')
    budget = pd.read_excel(Excel_name, sheet_name= 'Budget')

    #Paramter Dictionary
    l = {}
    for i in range(len(V1)):
        for j in range(len(T)):
            l[(V1[i], T[j])] = lower_bound.iloc[i,j+1]

    v = {}
    for i in range(len(V1)):
        for j in range(len(T)):
            v[(V1[i], T[j])] = value.iloc[i,j+1]

    c = {}
    for i in range(len(A)):
        for j in range(len(T)):
            c[(A[i], T[j])] = cost.iloc[i,j+1]

    m = {}
    for i in range(len(V1)):
        for j in range(len(T)):
            m[(V1[i], T[j])] = max_capacity.iloc[i,j+1]


    B = {}
    for i in range(len(T)):
            B[T[i]] = lower_bound.iloc[1,i+1]








    print(f'Scenario {scenario} and Test {test}:')


    #Model1
    b = {0: f}
    for i in V1:
        b[i] = 0

    objective_value, model1_time = build_model1(V, V1, A, T, T2, b, l, v, c, m, B)

    print(f'Model 1: Value = {objective_value}, Time = {model1_time} seconds')
    print(time.time() - begin)

    sht.write(k,0,scenario)
    sht.write(k,1,objective_value)
    sht.write(k,2,model1_time)




    #Reset b
    b = {0: f}
    for i in V1:
        b[i] = 0


    #Hueristic Model3
    step_size = 10
    first = 1
    last = first + step_size - 1
    total_objective = 0
    model3_time = 0

    while last <= num_time_periods:
        b, objective, runtime = build_model3(V, V1, A, first, last, b, l, v, c, m, B)
        first += step_size
        last = first + step_size - 1
        total_objective += objective
        model3_time += runtime

    print(f'Model 3: Value = {total_objective}, Time = {model3_time} seconds')
    print(time.time() - begin)

    sht.write(k,3,total_objective)
    sht.write(k,4,model3_time)


    k += 1




    book.save(f"Computational Results S3.xls")

