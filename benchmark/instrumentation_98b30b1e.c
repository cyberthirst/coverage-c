#include "instrumentation_98b30b1e.h"

void write_file_instrumentation_info_98b30b1e(char* file, int* arr, int len) {
    FILE* f = fopen("instrumentation_info_98b30b1e.txt", "a");
    fprintf(f, "%s:", file);
    for (int i = 0; i < len; i++) {
        fprintf(f, "%d", arr[i]);
        if (i < len - 1) {
            fprintf(f, ",");
        }
    }
    fprintf(f, "\n");
    fclose(f);
}

void write_instrumentation_info_98b30b1e() {
  write_file_instrumentation_info_98b30b1e("benchmark/fibo_uninstrumented.c", instrumentation_benchmark_fibo_uninstrumented_c, 15);
}
