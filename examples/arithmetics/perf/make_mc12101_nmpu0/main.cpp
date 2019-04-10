#include "nmpp.h"
#include "time.h"
#include "stdio.h"
#include "stdlib.h"

#pragma data_section ".data_imu0"
    long long L[2048];
#pragma data_section ".data_imu1"
    long long G[2048];
#pragma data_section ".data_imu2"
    long long im2[2048];
#pragma data_section ".data_imu3"
    long long im3[2048];
#pragma data_section ".data_em0"
    long long em0[2048];
#pragma data_section ".data_em1"
    long long em1[2048];

int main()
{
	printf("sdf");
  return 0;
}
