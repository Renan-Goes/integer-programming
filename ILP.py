from __future__ import print_function
from ortools.linear_solver import pywraplp
import re

class ILP_Solver():

    def __init__(self):
        self.solver = pywraplp.Solver.CreateSolver('SCIP')

    def read_data(self, filename):
        with open(filename, 'r', encoding='utf-8') as input_f:
            input_lines = input_f.readlines()

            self.number_of_products = int(re.findall(r'\b[0-9]+\b', input_lines[0])[0])
            self.number_of_materials = int(re.findall(r'\b[0-9]+\b', input_lines[1])[0])
            self.total_hours = int(re.findall(r'\b[0-9]+\b', input_lines[2])[0])
            self.time_change = int(re.findall(r'\b[0-9]+\b', input_lines[3])[0])
            self.cost_for_time = int(re.findall(r'\b[0-9]+\b', input_lines[4])[0])
            
            self.products = []

            for product_num in range(self.number_of_products):
                product = []
                values = re.findall(r'\b[0-9]+\.?[0-9]*\b', input_lines[6 + product_num])

                materials = []
                for material_num in range(self.number_of_materials):
                    materials.append(int(values[material_num]))

                product.append(materials)
                product.append(float(values[self.number_of_materials]))
                product.append(int(values[self.number_of_materials + 1]))
                product.append(int(values[self.number_of_materials + 2]))
                product.append(int(values[self.number_of_materials + 3]))
                
                self.products.append(product)

            self.materials = []

            for material_num in range(self.number_of_materials):
                self.materials.append([int(value) for value in re.findall(r'\b[0-9]+\.?[0-9]*\b', input_lines[7 + self.number_of_products + material_num])])

            return [self.number_of_products, self.number_of_materials, self.total_hours, self.time_change, self.cost_for_time,\
                self.products, self.materials]

    def get_variables(self): 
        self.solver = pywraplp.Solver.CreateSolver('SCIP')   
        self.status = self.solver.Solve()

        infinity = self.solver.infinity()
        self.variables = []
        for product_num in range(self.number_of_products):
            self.variables.append([self.solver.IntVar(0.0, infinity, f'n{product_num + 1}'), self.solver.IntVar(0.0, 1.0, f'k{product_num + 1}')])

        for material_num in range(self.number_of_materials):
            self.variables.append(self.solver.IntVar(0.0, infinity, f'w{material_num + 1}'))

        print(self.variables)

    def restriction_creations(self):
        for product_num in range(self.number_of_products):
            ### Dmin and Dmax restriction
            product_quantity = self.variables[product_num][0]
            product_exists = self.variables[product_num][1]
            dmin = self.products[product_num][2]
            dmax = self.products[product_num][3]

            self.solver.Add(product_exists*dmin <= product_quantity)
            self.solver.Add(product_exists*dmax >= product_quantity)

        ### Time restriction
            #self.solver.Sum([self.variables[product][0] = variable  of products to be used
            #self.products[product][1] = amount of hours per unit of product
            #self.variables[product][1] = variable if product is to be produced
        self.solver.Add(self.solver.Sum([self.variables[product][0]*self.products[product][1] for product in range(self.number_of_products)]) + \
            self.solver.Sum([self.variables[product][1] for product in range(self.number_of_products)])*self.time_change <= self.total_hours)

        ### Number of materials restriction
        for material_num in range(self.number_of_materials):
                #self.products[product][0][material_num] = number of material necessary for each product
                #self.variables[product][0] = variable  of products to be used
                #self.variables[self.number_of_products + material_num] = number of lots variable
                #self.materials[material_num][0] = number of materials per lot
            self.solver.Add(self.solver.Sum([self.products[product][0][material_num]*self.variables[product][0] for product in range(self.number_of_products)])\
                <= self.variables[self.number_of_products + material_num]*self.materials[material_num][0])

    def objective(self):
            #self.variables[product][0] = variable  of products to be used
            #self.products[product][4] = price per unit of products
            #self.variables[self.number_of_products + material] =  number of lots variable
            #self.materials[material][1] = cost per lot of material
        self.solver.Maximize(self.solver.Sum([self.variables[product][0]*self.products[product][4] for product in range(self.number_of_products)]) \
            - self.cost_for_time - self.solver.Sum([self.variables[self.number_of_products + material]*self.materials[material][1] for material in range(self.number_of_materials)]))

    def print_result(self):
        status = self.solver.Solve()
        if status == pywraplp.Solver.OPTIMAL:
            print('Solution:')
            print('Solution (profit) =', round(self.solver.Objective().Value()), '\n________________________')
            self.time_used = 0
            self.products_used_time = 0
            for variable in range(self.number_of_products):
                print(f'Product {variable + 1}:')
                print(self.variables[variable][0], '| Amount produced:', round(self.variables[variable][0].solution_value()), '| Total profit:', \
                    self.variables[variable][0].solution_value()*self.products[variable][4])
                print(self.variables[variable][1], round(self.variables[variable][1].solution_value()))
                self.products_used_time += self.variables[variable][1].solution_value()
                self.time_used += self.variables[variable][0].solution_value()*self.products[variable][1]
                print('_'*50)

            self.products_used_time *= self.time_change

            for variable in range(self.number_of_products, len(self.variables)):
                print(f'Raw material (lots):')
                print(self.variables[variable], round(self.variables[variable].solution_value()), '\n')
            
            print('Time used in production:', round(self.time_used), '| Time used in product change:', round(self.products_used_time))

ilpSolver = ILP_Solver()
data = ilpSolver.read_data('inputs/input3.txt')
print(data)
ilpSolver.get_variables()
ilpSolver.restriction_creations()
ilpSolver.objective()
print('_'*150)
print('_'*150)
ilpSolver.print_result()