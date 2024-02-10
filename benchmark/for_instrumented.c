#include "./instrumentation_98b30b1e.h"

int main() {
   if (atexit(write_instrumentation_info_98b30b1e)) return EXIT_FAILURE;
   instrumentation_forlop_for_uninstrumented_c[2] += 1; int cnt = 0;
   instrumentation_forlop_for_uninstrumented_c[3] += 1; for (int i = 0; i < 100000000; i++) {
       instrumentation_forlop_for_uninstrumented_c[4] += 1; cnt = cnt + 1;
    }
   instrumentation_forlop_for_uninstrumented_c[6] += 1; return cnt;
}