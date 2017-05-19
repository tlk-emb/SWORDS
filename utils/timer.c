
//#include <stdio.h>
#include "platform.h"

#define uint32_t unsigned int
#define CLOCK    unsigned int

/*
 *  MPCore Private Memory Region Base Address (Table 4.7 in ZYNQ manual)
 */
#define MPCORE_PMR_BASE  0xF8F00000

/*
 * Watchdog Timer Registers
 */
#define MPCORE_WDT_LR     (MPCORE_PMR_BASE + 0x0620)  /* Load register */
#define MPCORE_WDT_COUNT  (MPCORE_PMR_BASE + 0x0624)  /* Counter register */
#define MPCORE_WDT_CNT    (MPCORE_PMR_BASE + 0x0628)  /* Control register */
#define         MPCORE_WDT_CNT_EN        0x1
#define         MPCORE_WDT_CNT_AR        0x2
#define         MPCORE_WDT_CNT_IEN       0x4
#define         MPCORE_WDT_CNT_PS_OFFSET 0x8
#define MPCORE_WDT_ISR    (MPCORE_PMR_BASE + 0x062C)  /* Interrupt status register */
#define         MPCORE_WDT_ISR_SCBIT    0x01
#define MPCORE_WDT_RSR    (MPCORE_PMR_BASE + 0x0630)  /* Reset state register */
#define MPCORE_WDT_DR     (MPCORE_PMR_BASE + 0x0634)  /* Watchdog disable Register */

/*
 * Tmer preescaler and load value to achieve 1ms per tick.
 * Note that the preescaler value must be representable with 8 bits;
 * and the load value must be a 32bit value.
 *
 * Private timers and watchdogs are clocked with PERIPHCLK which is 1/2 of
 * the CPU frequency. The formula is:
 *
 *    period = (preescaler + 1)(load + 1) / PERIPHCLK
 *      - period    = 1ms
 *      - periphclk = 333.333MHz
 *
 * For example:
 *      - preescaler = 0
 *      - load       = 333332
 */
#define MPCORE_WDT_PS_1MS    0U       // preescaler for private watchdog
#define MPCORE_WDT_LOAD_1MS  333333332U  // load value for private watchdog

/*
 *  タイムティックの定義
 */
#define TIC_NUME  1U   /* タイムティックの周期の分子 */
#define TIC_DENO  1U   /* タイムティックの周期の分母 */

/*
 *  Convertion between the internal representation of the timer value
 *  and miliseconds/microseconds. One tick equals to 1ms.
 */
#define TIMER_CLOCK          MPCORE_WDT_LOAD_1MS // cycles
#define TO_CLOCK(nume, deno) (TIMER_CLOCK * (nume) / (deno))
//#define TO_USEC(clock)       (((SYSUTM) clock) * 1000U / TIMER_CLOCK)

/*
 *  32ビット単位の読出し／書込み
 */
inline uint32_t
sil_rew_mem(uint32_t *mem)
{
	uint32_t	data;

	data = *((volatile uint32_t *) mem);
	return(data);
}

inline void
sil_wrw_mem(uint32_t *mem, uint32_t data)
{
	*((volatile uint32_t *) mem) = data;
}

/*
 *  Get the current timer value
 */
inline CLOCK
target_timer_get_current(void)
{
        return(TO_CLOCK(TIC_NUME, TIC_DENO) -
                        sil_rew_mem((void *)MPCORE_WDT_COUNT));
}

/*
 *  Timer initialization
 */
void
target_timer_initialize(void)
{
        uint32_t cyc = TO_CLOCK(TIC_NUME, TIC_DENO);

        /* Stop the timer */
        sil_wrw_mem((void *)MPCORE_WDT_CNT, 0x00);

        /* Set it to timer mode */
        sil_wrw_mem((void *)MPCORE_WDT_DR, 0x12345678);
        sil_wrw_mem((void *)MPCORE_WDT_DR, 0x87654321);

        /* Stop the timer */
        sil_wrw_mem((void *)MPCORE_WDT_CNT, 0x00);

        /* Clear pending interrupts */
//        target_timer_int_clear();

        /* Set the counter value (1ms per tick) */
        sil_wrw_mem((void *)MPCORE_WDT_LR, cyc - 1);

        /*
         * Set the scaler for 1ms per tick and start the timer
         */
        sil_wrw_mem((void *)MPCORE_WDT_CNT,
              (MPCORE_WDT_PS_1MS << MPCORE_WDT_CNT_PS_OFFSET) |
               MPCORE_WDT_CNT_IEN | MPCORE_WDT_CNT_AR | MPCORE_WDT_CNT_EN);
}

/*
int main()
{
	volatile int	i;
	int		j = 0;
	int		tmp1, tmp2, tmp3;
    init_platform();

    print("\n\r=====\n\r\n\r");

    target_timer_initialize();

    while (1) {
    	printf("Hello World %d\n\r", j++);
    	tmp1 = target_timer_get_current();
    	tmp2 = target_timer_get_current();
        printf("\t\ttimer: %d\t%d\t%d\n\r", tmp1, tmp2 - tmp1, tmp1 - tmp3);
        tmp3 = tmp1;
    	for (i=0; i<100000000; i++)
    		;
    }
    print("Hello World\n\r");

    cleanup_platform();

    return 0;
}

//value / 3333333333 (sec)
 */

