import numpy as np
import pandas as pd
from multiprocess import Pool
import sys
import json
import os

# colors for each bacteria in the graphics
colors = {"coop": "blue", "cheat": "red"}

# bacteria class (agent) - CA
class Bacteria:
    def __init__(self, energy, recombination, breed, loc):
        # int for bacteria energy
        self.energy = energy
        # boolean for if it takes part in recombination
        self.recombination = recombination
        # int for breed
        self.breed = breed
        # list of ints for location [x, y]
        self.loc = loc
        # string for the color according to the breed
        self.color = colors[breed]
    
    # method to set color based on breed
    def set_breed(self, breed):
        self.breed = breed
        self.color = colors[breed]

    # method to get possible move options
    def get_move_options(self, size):
        options = []  # to store possible move options
        # check if x-coordinate is not at left edge of grid
        if self.loc[0] != 0:
            options.append([self.loc[0] - 1, self.loc[1]])
        # check if x-coordinate is not at right edge of grid
        if self.loc[0] != size[0] - 1:
            options.append([self.loc[0] + 1, self.loc[1]])
        # check if y-coordinate is not at top edge of grid
        if self.loc[1] != 0:
            options.append([self.loc[0], self.loc[1] - 1])
        # check if y-coordinate is not at bottom edge of grid
        if self.loc[1] != size[1] - 1:
            options.append([self.loc[0], self.loc[1] + 1])
        return options
    
# simulation class - we can remove print statements, only for testing - CA
# TODO: add tracking and return of simulation data over generations
# TODO: add animation of simulation based on tracking of data over generations    
# simulation class
class Sim:
    def __init__(self, 
                 start_energy, 
                 population_size, 
                 population_viscosity, 
                 recombination_cost,
                 mutation_rate, 
                 recombination_rate, 
                 percent_recombination, 
                 percent_cooperation,
                 contribution, 
                 multiplier, 
                 max_x, 
                 max_y):
        
        # attribute initialization
        self.start_energy = start_energy  # energy is consumed over time. when energy is 0, bacteria dies
        self.population_size = population_size  # when cells die, remaining cells reproduce to keep population size constant
        self.population_viscosity = population_viscosity  # no of gens each cell remains in same loc before moving to adjacent loc
        self.recombination_cost = recombination_cost  # subtracts from resources available to each cell that recombines
        self.mutation_rate = mutation_rate  # rate at which coops produce cheat offspring
        self.recombination_rate = recombination_rate  # rate at which recombs change phenotype of other cells in same loc (coops make others coop, cheats make others cheat, converted cells are also recomb)
        self.percent_recombination = percent_recombination  # initial percent of recombiners
        self.percent_cooperation = percent_cooperation  # initial percent of cooperators
        self.contribution = contribution  # all coops contribute some fitness to common pool
        self.multiplier = multiplier  # common pool value is multiplied (benefit of cooperation)
        self.max_x = max_x  # x-coordinate of grid
        self.max_y = max_y  # y-coordinate of grid
        
        # list to store bacteria
        self.bacteria = []

        # number of recombination and cooperation bacteria
        self.num_rec = int(np.round(population_size * percent_recombination))  # total population size * percent recombiners, round to nearest int
        self.num_coop = int(np.round(population_size * percent_cooperation))  # total population size * percent cooperators, round to nearest int

        np.random.seed(0)

        # randomly assign recombination and cooperation to bacteria
        index_rec = np.random.choice(population_size, self.num_rec, replace=False)
        index_coop = np.random.choice(population_size, self.num_coop, replace=False)

        # create bacteria
        for i in np.arange(population_size):
            bac = Bacteria(start_energy, True if i in index_rec else False, "coop" if i in index_coop else "cheat",
                           [np.random.choice(max_x, 1)[0], np.random.choice(max_y,1)[0]])
            self.bacteria.append(bac)
    
    # method to simulate a generation
    def simulate_gen(self, gen):
        #print("starting gen", gen)
        # coops contribute public goods at the cost of energy
        def contribute(bac):
            if bac.breed == "coop":
                bac.energy -= self.contribution  # coops lose energy
            return bac
        # apply contribute function to all bacteria
        print("contribute")
        with Pool(64) as pool:
            self.bacteria = pool.map(contribute, self.bacteria)

        # all cells benefit from public good
        amt = (self.num_coop * self.multiplier) / len(self.bacteria)
        def benefit(bac):
            bac.energy += amt
            return bac
        # apply benefit function to all bacteria
        print("benifit")
        with Pool(64) as pool:
            self.bacteria = pool.map(benefit, self.bacteria)
        
        # cells lose energy
        def update_fitness(bac):
            # random energy decrease
            if np.random.choice(2, 1) == 1:
                bac.energy -= 1
            # recombiners lose additional energy
            if bac.recombination:
                bac.energy -= self.recombination_cost
            return bac
        # apply update_fitness function to all bacteria
        print("fitness")
        with Pool(64) as pool:
            self.bacteria = pool.map(update_fitness, self.bacteria)

        # bacteria die if energy is < 0
        alive_bac = []  # to store bacteria that are alive
        def kill(b):
            # bacteria with energy < 0 die
            if b.energy < 0:
                if b.breed == "coop":
                    self.num_coop -= 1  # decrease number of coops
                if b.recombination:
                    self.num_rec -= 1  # decrease number of recombiners
            else:
                alive_bac.append(b)  # if energy > 0, add bacteria to alive_bac list (includes cheaters)
        # update bacteria list
        with Pool(64) as pool:
            pool.map(kill, self.bacteria)
        self.bacteria = alive_bac

        # if no bacteria are left, method returns early
        if len(self.bacteria) == 0:
            return

        # reproduction
        # reproduce until population size is reached
        while len(self.bacteria) < self.population_size:
            # randomly select parent
            parent = self.bacteria[np.random.choice(len(self.bacteria), 1)[0]]
            # randomly select whether to mutate or not
            ## draw 1 sample from [0,1] array with probabilities (1-mutation_rate) and (mutation_rate)
            ## 0 means no mutation, 1 means mutation
            mutate = np.random.choice(2, 1, p=[1 - self.mutation_rate, self.mutation_rate])[0]
            # if mutation does not occur:
            if mutate == 0:  # child has same breed as parent
                breed = parent.breed 
            # if mutation occurs:
            elif parent.breed == "coop":  # if parent is coop, child is cheat
                breed = "cheat"
            else:
                breed = "coop"  # if parent is cheat, child is coop
            if breed == "coop":  # if child is coop, increase number of coops
                self.num_coop += 1
            if parent.recombination:  # if parent is recombiner, child is recombiner
                self.num_rec += 1
            # create child
            bac = Bacteria(parent.energy, parent.recombination, breed, parent.loc)
            # add child to bacteria list
            self.bacteria.append(bac)

        # conversion/recombination
        if self.num_rec != 0:
            # cells in each location
            bac_locs = {}
            # number of recombiners in each location
            bac_rec = {}

            # group bacteria by location
            def locate_bac(b):
                # if location is already in bac_locs, append bacteria to list
                if str(b.loc) in bac_locs.keys():
                    bac_locs[str(b.loc)].append(b)
                    # if bacteria is recombiner, increase count of recombiners in location
                    if b.recombination:
                        bac_rec[str(b.loc)] += 1
                # if location is not in bac_locs, create new list with bacteria
                else:
                    # if bacteria is recombiner, set count of recombiners in location to 1
                    bac_locs[str(b.loc)] = [b]
                    if b.recombination:
                        bac_rec[str(b.loc)] = 1
                    # if bacteria is not recombiner, set count of recombiners in location to 0
                    else:
                        bac_rec[str(b.loc)] = 0
            print("locate")
            with Pool(64) as pool:
                pool.map(locate_bac, self.bacteria)

            # recombination
            def recombine(k):
                # if no recombiners in location or all bacteria are recombiners, skip location
                if bac_rec[k] == 0 or bac_rec[k] == len(bac_locs[k]):
                    return
                # for each bacteria in location
                for b in bac_locs[k]:
                    # if bacteria is not yet a recombiner:
                    if not b.recombination:
                        # pick whether to recombine or not for each recombiner based on recombination rate
                        recombine = np.random.choice(2, bac_rec[k], p=[1-self.recombination_rate, self.recombination_rate])
                        # if any bacteria recombine, increment number of recombiners
                        if np.sum(recombine) > 0:
                            b.recombination = True
                            self.num_rec += 1
            print("recombine")
            with Pool(64) as pool:
                pool.map(recombine, bac_locs.keys())

        # movement
        ## bacteria move to adjacent location every population_viscosity generations
        if (gen + 1) % self.population_viscosity == 0:
            def move_bac(b):
                # use get_move_options method defined previously to get possible move options
                move_ops = b.get_move_options([self.max_x, self.max_y])
                # randomly select new location from possible move options
                b.loc = move_ops[np.random.choice(len(move_ops), 1)[0]]
            print("movement")
            with Pool(64) as pool:
                pool.map(move_bac, self.bacteria)

    # method to simulate generations    
    def simulate(self, gens):
        #print("starting simulation")
        for g in np.arange(gens):
            self.simulate_gen(g)
            if len(self.bacteria) == 0:
                #print("all dead")
                break
            #print("***results after gen***", g)
            #for b in self.bacteria:
                #print(b.recombination)
                #print(b.breed)
                #print(b.energy)
                #print(b.loc)

if __name__ == '__main__':
    pop_size = int(sys.argv[1]) # np.arange(100, 500, 100)
    stay = int(sys.argv[2]) # np.arange(1, 4, 2)
    rec_cost = int(sys.argv[3]) # np.arange(0, 3, 1)
    rec_rate = float(sys.argv[4]) # np.arange(0.01, 0.11, 0.03)
    multiplier = int(sys.argv[5]) # np.arange(1, 6, 2)

    json_path = f'sim_{pop_size}_{stay}_{rec_cost}_{rec_rate}_{multiplier}.json'
    count = 0
    if os.path.exists(json_path):
        with open((json_path), 'r') as f:
            for line in f:
                count += 1
    print("there have already been", count, "simulations")
    for i in range(5 - count):
        print("simulating", i)
        sim = Sim(
            start_energy=2,
            population_size=pop_size,
            population_viscosity=stay,
            recombination_cost=rec_cost,
            mutation_rate=0.001,
            recombination_rate=rec_rate,
            percent_recombination=0.5,
            percent_cooperation=0,
            contribution=1,
            multiplier=multiplier,
            max_x=5,
            max_y=5
        )
        sim.simulate(50)
        result = {
            'rec_rate': rec_rate,
            'multiplier': multiplier,
            'rec_cost': rec_cost,
            'stay': stay,
            'pop_size': pop_size,
            'count_As': sum(1 for b in sim.bacteria if b.breed == 'coop'),
            'count_Ss': sum(1 for b in sim.bacteria if b.breed == 'cheat'),
            'count_As_recomb': sum(1 for b in sim.bacteria if b.breed == 'coop' and b.recombination),
            'count_Ss_recomb': sum(1 for b in sim.bacteria if b.breed == 'cheat' and b.recombination)
        }
        with open(json_path, 'a') as json_file:
            json_file.write(json.dumps(result) + '\n')