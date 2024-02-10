#include "./instrumentation_98b30b1e.h"
#include <stdio.h>

long fibonnaci (long n) {
   instrumentation_benchmark_fibo_uninstrumented_c[3] += 1; if (n == 0) {
       instrumentation_benchmark_fibo_uninstrumented_c[4] += 1; return 0;
    }
   instrumentation_benchmark_fibo_uninstrumented_c[6] += 1; if (n == 1) {
       instrumentation_benchmark_fibo_uninstrumented_c[7] += 1; return 1;
    }
   instrumentation_benchmark_fibo_uninstrumented_c[9] += 1; return fibonnaci(n-1) + fibonnaci(n-2);
}

int main() {
   if (atexit(write_instrumentation_info_98b30b1e)) return EXIT_FAILURE;
   instrumentation_benchmark_fibo_uninstrumented_c[13] += 1; fibonnaci(33);
}
