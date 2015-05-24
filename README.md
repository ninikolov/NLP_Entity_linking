#NLP Entity linking Project - Team Entity Rangers

Execute baseline version by putting *original* crosswikis file into the data directory and running:
###For first baseline: 

	cd src/baseline/
	python3 baseline.py
	
###For second baseline: 

	cd src/baseline/
	python3 tagme_server.py

###For our implementation of Tagme (may take a while if you don't have the cache): 

	cd src/algorithms/
	python3 tagme.py
	
###For dynamic programming solution (may take a while if you don't have the cache):

	cd src/algorithms/

Change last line of dynamic_prog.py. 
	
	python3 dynamic_prog.py
	
###For combined solution (may take a while if you don't have the cache): 

	cd src/algorithms/
	
Change last line of dynamic_prog.py. 
	
	python3 dynamic_prog.py

