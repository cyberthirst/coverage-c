#ifndef INSTRUMENTATION_98b30b1e_H
#define INSTRUMENTATION_98b30b1e_H
#include<stdio.h>
#include<stdlib.h>

int instrumentation_benchmark_fibo_uninstrumented_c[15];
void write_file_instrumentation_info_98b30b1e(char* file, int* arr, int len);
void write_instrumentation_info_98b30b1e();
#endif
