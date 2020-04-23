import PetrieSimulator


# step 1 - create the simulation
sim = PetrieSimulator(50, 0.2, 0.2)

# step 2 - run the simulation
sim.run(5)

# step 3 - print the results
sim.print_model_statistics()
