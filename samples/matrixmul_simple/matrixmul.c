#define P 32

int matrixmul_soft(int a[P][P], int b[P][P], int c[P][P]){
  int i,j,k;

  for (i = 0; i < P; i++){
    for (j = 0; j < P; j++){
      c[i][j] = 0;
      for (k = 0; k < P; k++){
        c[i][j] += a[i][k] * b[k][j];
      }
    }
  }

  return 0;

}
int matrixmul(int a[P][P],
    int b[P][P],
    int c[P][P]){
  int i,j,k;
  for (i = 0; i < P; i++){
    for (j = 0; j < P; j++){
      c[i][j] = 0;
      for (k = 0; k < P; k++){
        c[i][j] += a[i][k] * b[k][j];
      }
    }
  }
  return 0;
}

int main()
{

  XTime tStart1, tEnd1;
  XTime tStart2, tEnd2;
  XTime tStart3, tEnd3;

  init_platform();

  printf("Hello! matrixmul\n\r");
  int i,j;

  XTime_GetTime(&tStart1);

  srand(tStart1);

  int a[P][P], b[P][P], c[P][P], d[P][P], e[P][P];

  for (i = 0;i < P;i++){
    for (j = 0; j < P;j++){

      a[i][j] = (int)rand() % 256;
      b[i][j] = (int)rand() % 256;
    }
  }

  Xil_DCacheDisable();

  matrixmul(a,b,d);

  XTime_GetTime(&tStart1);
  matrixmul_interrupt(a,b,c);
  XTime_GetTime(&tEnd1);

  XTime_GetTime(&tStart2);
  matrixmul(a,b,d);
  XTime_GetTime(&tEnd2);

  Xil_DCacheEnable();

  XTime_GetTime(&tStart3);
  matrixmul_soft(a,b,e);
  XTime_GetTime(&tEnd3);

  for (i = 0;i < P;i++){
    for (j = 0; j < P;j++){
      if (c[i][j] != d[i][j]) {
        printf("a[%d][%d] = %d\t",i,j,a[i][j]);
        printf("b[%d][%d] = %d\t",i,j,b[i][j]);
        printf("c[%d][%d] = %d\t",i,j,c[i][j]);
        printf("d[%d][%d] = %d\t",i,j,d[i][j]);
        printf("e[%d][%d] = %d\n",i,j,e[i][j]);
      }
    }
  }


  printf("hard interr time: %llu\n",2*(tEnd1-tStart1));
  printf("hard poling time: %llu\n",2*(tEnd2-tStart2));
  printf("soft time       : %llu\n",2*(tEnd3-tStart3));

  printf("end matrixmul\n\r");

  cleanup_platform();
  return 0;
}
