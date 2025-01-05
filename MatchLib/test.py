from MatchLib import *

# Initialize matchlib
init_matchlib("http://localhost:5000", 99, verbose=True)

wait_for_connection()
print("Connected to VPFS")

wait_for_match()
print("Match started")

while not is_match_finished():
    # Do stuff
    pass

print("Match Finished")