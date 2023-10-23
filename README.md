# Setup
1. script was tested with `Python3.8`
2. supported OS: Linux, MacOS
3. requires `gcc`

### Install dependencies
1. pip install pycparser

# Usage
- Usage: python src/cov.py [OPTIONS]
- Get help: python src/cov.py --help

```
Options:
  -f, --input-file <FILE>
  -d, --input-dir <DIR>
  -D, --output-dir <FILE>
  -F, --output-file <DIR>
  -i, --input-args [INPUT_ARGS ...]
```
### Example run & basic explanation
* python src/cov.py -d src/c_files/suite3/ -D out
  * takes input directory `src/c_files/suite3`
  * copies the input directory to output directory `out` (while keeping the original directory structure)
  * modifies the `.c` files in `out`
  * compiles the `.c` files
  * runs the binary with the provided input arguments (in this case no input args)
    * this outputs coverage info
  * coverage info is parsed and `lcov.info` is created
  * `lcov.info` is stored in the orginal input directory

# What it can do
 - [x] Line coverage on statements without loops and conditions
 - [x] Line coverage on statements with loops and conditions
 - [x] Line coverage on a file with a main function
 - [x] Line coverage on several files
 - [ ] The code is tested 
 - [ ] Benchmark

# Testing
- the script currently lacks proper testing
- we provide 3 very basic `C` test suites in `src/c_files` that can be used to see how the coverage work
# Known issues
- line coverage is limited, if we have multiple statements on one line, then the coverage displayed is for the 1st statement
- we don't support condition or branch coverage
- coverage is based on the execution from the `main` function, we don't support integration with testing framework

# Acknowledgment
- `fake_libc_include` was extracted from the pycparser library, available at: https://github.com/eliben/pycparser/tree/master/pycparser