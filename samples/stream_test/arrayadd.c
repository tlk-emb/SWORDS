#define P 50

void arrayadd_soft(int a[P], int b{P}){
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

	int tmp1,tmp2,tmp3,tmp4,tmp5,tmp6;

    init_platform();

    //Xil_DCacheDisable();

    printf("Hello! matrixmul\n\r");
    int i,j;

    target_timer_initialize();

    srand(target_timer_get_current());

    int a[P], b[P], c[P], d[P];

    for (i = 0;i < P;i++){
    	a[i] = i;
    }

    target_timer_initialize();

    tmp1 = target_timer_get_current();

    arrayadd_interrupt(a,b);

    tmp2 = target_timer_get_current();

    target_timer_initialize();

    tmp3 = target_timer_get_current();

    arrayadd(a,c);

    tmp4 = target_timer_get_current();

    Xil_DCacheEnable();

    target_timer_initialize();

    tmp5 = target_timer_get_current();

    arrayadd_soft(a,d);

    tmp6 = target_timer_get_current();

    
    printf("hard interr time:%d\n",tmp2 - tmp1);
    printf("hard poling time:%d\n",tmp4 - tmp3);
    printf("soft time:%d\n",tmp6 - tmp5);

    printf("end matrixmul\n\r");

    cleanup_platform();
    return 0;
}
