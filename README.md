# An agent-based model of recombination and prosocial behavior in bacteria #
_By Cassandra Areff, Yumi Briones, Alyssa Pradhan, and Danielle Share_

## GOAL ##
We aim to replicate the agent-based model of prosocial behavior and recombination in bacteria by Lee et al. (2023) using Python packages. We will run a minimal subset of parameter combinations and
compare our findings to the original paper.

## DIRECTORY STRUCTURE ##

* `run_sim.py` is our simulation with parallel computing features
* `gens_50` contains `run_sim.py` results for 50 generations
* `gens_500` contains `run_sim.py` results for 500 generations
* `test_sims` are test simulation results
* `abm.ipynb` is the initial version of our simulation in notebook format, without parallel computing features
* `241212_vis` generates visualizations from `gens_50`
* `test_visualizations` contains test code for visualizations

## REFERENCES ##
P. A. Lee, O. T. Eldakar, J. P. Gogarten, and C. P. Andam. *Recombination as an enforcement
mechanism of prosocial behavior in cooperating bacteria.* Iscience, 26(8), 2023.
