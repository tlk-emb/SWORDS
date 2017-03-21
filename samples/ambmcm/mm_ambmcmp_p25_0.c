#define PROJECT "mm_ambmcmp_p25_0"
#include "string.h"
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
int matrixmul(int a[P][P], int b[P][P], int c[P][P]){
   int i,j,k;
#pragma HLS ARRAY_PARTITION variable=c dim=2
   for (i = 0; i < P; i++){
		for (j = 0; j < P; j++){
#pragma HLS PIPELINE II=25
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

	int tmp1,tmp2,tmp3,tmp4,tmp5,tmp6;

    init_platform();

    //Xil_DCacheDisable();

    printf("Hello! (%s)\n\r",PROJECT);
    int i,j;

    target_timer_initialize();

    srand(target_timer_get_current());

    int a[P][P], b[P][P], c[P][P], d[P][P], e[P][P];

    for (i = 0;i < P;i++){
    	for (j = 0; j < P;j++){

    		a[i][j] = (int)rand() % 256;
    		b[i][j] = (int)rand() % 256;
    	}
    }

    target_timer_initialize();

    tmp1 = target_timer_get_current();

    matrixmul_interrupt(a,b,c);

    tmp2 = target_timer_get_current();

    target_timer_initialize();

    tmp3 = target_timer_get_current();

    matrixmul(a,b,d);

    tmp4 = target_timer_get_current();

    Xil_DCacheEnable();

    target_timer_initialize();

    tmp5 = target_timer_get_current();

    matrixmul_soft(a,b,e);

    tmp6 = target_timer_get_current();

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


    printf("hard interr time:%d\n",tmp2 - tmp1);
    printf("hard poling time:%d\n",tmp4 - tmp3);
    printf("soft time:%d\n",tmp6 - tmp5);

    printf("(%s)\n\r",PROJECT);

    cleanup_platform();
    return 0;
}
