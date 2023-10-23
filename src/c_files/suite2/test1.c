#include <stdio.h>

int my_global = 45;

int test() { return 0; }
int doubler(int x)
{
    int y = x + 1;
    for (int i = 0; i < 10; i++)
    {
        printf("%d\n", i);
    }
    return x * 2;
}

int main(int argc, char **argv)
{
    printf("Hello %d", doubler(6));
    return 0;
}
