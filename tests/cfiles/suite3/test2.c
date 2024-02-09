#include <stdio.h>

long factorial(long n)
{
    if (n == 0)
    {
        return 1;
    }
    else
    {
        return n * factorial(n - 1);
    }
}

int main(int argc, char **argv)
{
    if (argc <= 1)
    {
        printf("Please input a number.\n");
    }
    else
    {
        long n = 0;
        sscanf(argv[1], "%ld", &n);

        printf("The factorial of %ld is %ld.\n", n, factorial(n));
    }
    return 0;
}
