#include "xtime_l.h"
#define P 64

int mul(int x[P], int y[P], int z[P]){
  int i;

  for (i = 0; i < P; i++)
    z[i] = x[i] * y[i];

  return 0;
}

int add(int x[P], int y[P]){
  int i;

  for (i = 0; i < P; i++)
    y[i] += x[i];

  return 0;
}

int madd(int x[P], int y[P], int z[P]){
  int i;
  int t[P];

  mul(x, y, t);
  add(t, z);

  return 0;
}

int madd_soft(int x[P], int y[P], int z[P]){
  int i;
  int t[P];

  mul(x, y, t);
  add(t, z);

  return 0;
}

int main()
{
  int a[P],b[P],c[P],d[P];
  int i;
  
  XTime tStart1, tEnd1;
  XTime tStart2, tEnd2;
  
  XTime_GetTime(&tStart1);
  srand(tStart1);

  for (i = 0;i < P;i++){
    a[i] = (int)rand() % 256;
    b[i] = (int)rand() % 256;
    c[i] = (int)rand() % 256;
    d[i] = c[i];
  }
  
  init_platform();

  printf("Hello! madd\n\r");

  XTime_GetTime(&tStart1);
  madd(a, b, c);
  XTime_GetTime(&tEnd1);

  XTime_GetTime(&tStart2);
  madd_soft(a, b, d);
  XTime_GetTime(&tEnd2);

  for (i=0; i<P; i++){
    printf("hw[%d] = %d\t",i,c[i]);
    printf("sw[%d] = %d\n",i,d[i]);
  }

  printf("hard interr time: %llu\n",2*(tEnd1-tStart1));
  printf("soft time       : %llu\n",2*(tEnd2-tStart2));

  printf("end madd\n\r");

  cleanup_platform();

  return 0;
}
