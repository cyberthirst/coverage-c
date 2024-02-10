# Setup
1. script was tested with `Python3.8`
2. supported OS: Linux, MacOS
3. requires `gcc`

### Installation
- `pip install .`
- will install the package as `ccov` (see `setup.py`)

# Usage
- Usage: `ccov [OPTIONS]`
- Get help: `ccov --help`

```
Options:
  -f, --input-file <FILE>
  -d, --input-dir <DIR>
  -D, --output-dir <FILE>
  -F, --output-file <DIR>
  -i, --input-args [INPUT_ARGS ...]
```
## Example run & basic explanation
* `ccov -d src/c_files/suite3/ -D out`
  * takes input directory `src/c_files/suite3`
  * copies the input directory to output directory `out` (while keeping the original directory structure)
  * modifies the `.c` files in `out`
  * compiles the `.c` files
    * compiled with: `command = ["gcc", "-O0", "-o", executable_path] + c_files`
  * runs the binary with the provided input arguments (in this case no input args)
    * this outputs coverage info
  * coverage info is parsed and `lcov.info` is created
  * `lcov.info` is stored in the orginal input directory

# Features
 - [x] Line coverage on statements without loops and conditions
 - [x] Line coverage on statements with loops and conditions
 - [x] Line coverage on a file with a main function
 - [x] Line coverage on several files
 - [x] The code is tested 
 - [x] Benchmark

# Testing
- we provide 3 very basic `C` test suites in `src/c_files` that can be used for system testing
- additionally, unit tests are provided in `tests/`
## Coverage
- `chmod +x ./run_coverage.sh`
- `./run_coverage.sh`

| Name                   | Stmts | Miss | Cover   |
|------------------------|-------|------|---------|
| src/cov.py             | 100   | 25   | 75%     |
| src/instrumentation.py | 77    | 17   | 78%     |
| src/utils.py           | 15    | 8    | 47%     |
| src/visitors.py        | 50    | 8    | 84%     |
| **TOTAL**              | 242   | 58   | **76%** |



# Benchmark
- we currently lack benchmarking
- benchmark was done on the programs in `benchmark/` and can be run with `./run_benchmark.sh`
- results are:
```
Benchmarking programs...
fibo_uninstrumented average runtime: .036 ms
fibo_instrumented average runtime: .036 ms
On average, the instrumented version of fibo is faster by 0 ms
---------------------------------
for_uninstrumented average runtime: .108 ms
for_instrumented average runtime: .220 ms
On average, the instrumented version of for is slower by .112 ms

```
- we assume that in the `fibo` case, the most time is spent on the recursive part - creating the function frames, and thus the instrumentation has no effect
- in the `for` case, the instrumentation has a significant effect on the runtime, as the program is slowed down basically 2x
  - this is because the body of the for loop contains one additional `ADD` instruction (to increase the array element), and thus has 2x computational complexity

# Known issues
- line coverage is limited, if we have multiple statements on one line, then the coverage displayed is for the 1st statement
- we don't support condition or branch coverage
- coverage is based on the execution from the `main` function, we don't support integration with testing framework

# Acknowledgment
- `fake_libc_include` was extracted from the pycparser library, available at: https://github.com/eliben/pycparser/tree/master/pycparser