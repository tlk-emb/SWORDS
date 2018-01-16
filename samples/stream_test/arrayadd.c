#include "xtime_l.h"
#define P 50

void arrayadd_soft(int a[P], int b[P]){
	int i;
	for(i = 0; i < P; i++){
		b[i] = a[i] + 5;
	}
	//return 0;
}

void arrayadd(int a[P], int b[P]){
	int i;
	for(i = 0; i < P; i++){
		b[i] = a[i] + 5;
	}
	//return 0;
}

int main()
{

	XTime tStart1, tEnd1;
    XTime tStart2, tEnd2;
    XTime tStart3, tEnd3;

    init_platform();

    //Xil_DCacheDisable();

    printf("Hello! stream_test\n\r");
    int i,j;

    XTime_GetTime(&tStart1);
    srand(tStart1);

    int a[P], b[P], c[P], d[P];

    for (i = 0;i < P; i++){
    	a[i] = (int)rand() % 256;
    }

    XTime_GetTime(&tStart1);
    arrayadd_interrupt(a,b);
    XTime_GetTime(&tEnd1);

    XTime_GetTime(&tStart2);
    arrayadd(a,c); 
    XTime_GetTime(&tEnd2);
    
    XTime_GetTime(&tStart3);
    arrayadd_soft(a,d);
    XTime_GetTime(&tEnd3);

    for (i = 0;i < P;i++){
        if (b[i] != d[i] || c[i] != d[i]){
            printf("b[%d] = %d\t",i,b[i]);
            printf("c[%d] = %d\t",i,c[i]);
            printf("d[%d] = %d\n",i,d[i]);
        }
    }
    printf("hard interr time: %llu\n",2*(tEnd1-tStart1));
    printf("hard poling time: %llu\n",2*(tEnd2-tStart2));
    printf("soft time       : %llu\n",2*(tEnd3-tStart3));

    printf("end stream_test\n\r");

    cleanup_platform();
    return 0;
}
