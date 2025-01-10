# Compare two trigger reports

import sys

#--------------------------------------------------------------
# Fill the log results
def fill_results(f, verbose = 0):
    results = {}

    timing_info = []
    for line in f:
        if verbose > 1: print(line)
        # Exit once the trigger path summary has completed
        if 'End-path summary' in line: break
        words = line.split()
        # Check if it's the timing information
        if len(words) == 8 and words[0] == "Full" and words[1] == "event":
            #             [min, avg, max, median, rms]
            timing_info = [float(words[index]) for index in range(2,7)]
            if verbose > 0:
                print("Timing info:    min        avg        max       median     rms")
                print("             %.3e  %.3e  %.3e  %.3e  %.3e" % (timing_info[0], timing_info[1], timing_info[2],
                                                               timing_info[3], timing_info[3]))
                print("Path                          :    run   pass   fail  error")
            continue
        # Check if it's a trigger path summary line
        if len(words) != 7 or words[0] != 'TrigReport': continue
        try:
            #        [run, pass, fail, error]
            counts = [int(words[index]) for index in range(2,6)]
            path   = words[-1]
            results[path] = counts
            if verbose > 0:
                print("%30s: %6i %6i %6i %6i" % (path, counts[0], counts[1], counts[2], counts[3]))
        except: continue
    return results,timing_info

#--------------------------------------------------------------
# Main execution
if len(sys.argv) < 3:
    print("Not enough arguments! Useage: python check_trigger_results.py <file_1> <file_2> [verbose level, default = 0]")
    exit(2)
verbose = int(sys.argv[3]) if len(sys.argv) == 4 else 0

file_1 = sys.argv[1] # Local log file
file_2 = sys.argv[2] # Reference log file
try:
    f_1 = open(file_1,'r')
    f_2 = open(file_2,'r')
except FileNotFoundError:
    print("Files were not both found!")
    exit(2)

if verbose > 0: print(">>> Retrieving info from the local processing")
results_1,timing_1 = fill_results(f_1, verbose)
if verbose > 0: print(">>> Retrieving info from the reference processing")
results_2,timing_2 = fill_results(f_2, verbose)

# Define the major vs. minor failure thresholds
count_minor_threshold = 1 # path rate change for minor failure
count_major_threshold = 4 # path rate change for major failure
avg_time_minor_threshold = 0.15 # fractional change in time / event
avg_time_major_threshold = 0.25 # fractional change in time / event
minor_fail = False
major_fail = False

# Check the path rates
for path in results_1:
    if path in results_2:
        counts_1 = results_1[path]
        counts_2 = results_2[path]
        for index in range(len(counts_1)):
            delta = abs(counts_1[index] - counts_2[index])
            if delta >= count_major_threshold:
                major_fail = True
                print(">>> Path " + path + " has a major change!")
                print("Local counts    :", counts_1)
                print("Reference counts:", counts_2)
            elif delta >= count_minor_threshold:
                minor_fail = True
                print(">>> Path " + path + " has a minor change:")
                print("Local counts    :", counts_1)
                print("Reference counts:", counts_2)
    else:
        print(">>> New trigger path " + path + " in local found, not in the reference!")
        major_fail = True
for path in results_2:
    if path not in results_1:
        print(">>> Trigger path " + path + " in reference not found in local!")
        major_fail = True

# Check the timing rates
avg_time_delta = abs(timing_1[1]/timing_2[1] - 1.)
if avg_time_delta > avg_time_major_threshold:
    print(">>> Average time changed significantly: %.4f (new) vs. %.4f (reference)" % (timing_2[1], timing_1[1]))
    major_fail = True
elif avg_time_delta > avg_time_minor_threshold:
    print(">>> Average time changed somewhat significantly: %.4f (new) vs. %.4f (reference)" % (timing_2[1], timing_1[1]))
    minor_fail = True

# Return the exit codes for minor/major failures
if major_fail: exit(2)
if minor_fail: exit(1)

# No failures
print("No problems detected")
exit(0)
