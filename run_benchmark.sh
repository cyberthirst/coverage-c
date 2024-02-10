#!/bin/bash

# Navigate to the benchmark directory
cd benchmark || exit

# List of programs to benchmark
programs=("fibo" "for")
runs=20

echo "Benchmarking programs..."

for prog in "${programs[@]}"; do
    uninstrumented_total_time=0
    instrumented_total_time=0

    # Run the uninstrumented version 20 times
    for ((i=1; i<=runs; i++)); do
        start_time=$(python -c "import time; print(time.time())")
        #echo "start time: $start_time"
        ./${prog}_uninstrumented
        end_time=$(python -c "import time; print(time.time())")
        #echo "end time: $end_time"
        runtime=$(echo "scale=3; ($end_time - $start_time)" | bc)
        uninstrumented_total_time=$(echo "$uninstrumented_total_time + $runtime" | bc)
    done

    #echo "===================="

    # Run the instrumented version 20 times
    for ((i=1; i<=runs; i++)); do
        #start_time=$(date +%s%N)
        start_time=$(python -c "import time; print(time.time())")
        ./${prog}_instrumented
        #end_time=$(date +%s%N)
        end_time=$(python -c "import time; print(time.time())")
        runtime=$(echo "scale=3; ($end_time - $start_time)" | bc)
        instrumented_total_time=$(echo "$instrumented_total_time + $runtime" | bc)
    done

    # Calculate average runtime
    uninstrumented_avg=$(echo "scale=3; $uninstrumented_total_time / $runs" | bc)
    instrumented_avg=$(echo "scale=3; $instrumented_total_time / $runs" | bc)

    echo "${prog}_uninstrumented average runtime: $uninstrumented_avg ms"
    echo "${prog}_instrumented average runtime: $instrumented_avg ms"

    # Compare the average runtimes
    if (( $(echo "$uninstrumented_avg < $instrumented_avg" | bc) )); then
        slower_by=$(echo "$instrumented_avg - $uninstrumented_avg" | bc)
        echo "On average, the instrumented version of $prog is slower by $slower_by ms"
    else
        faster_by=$(echo "$uninstrumented_avg - $instrumented_avg" | bc)
        echo "On average, the instrumented version of $prog is faster by $faster_by ms"
    fi
    echo "---------------------------------"
done

# Navigate back to the original directory
cd - > /dev/null
