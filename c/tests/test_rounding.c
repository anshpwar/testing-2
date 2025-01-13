#include <stdint.h>

#include "check.h"
#include "lk_money.h"

static int64_t rd(int64_t n, int64_t d, int mode) {
    int64_t out = 12345;
    int rc = lk_round_div(n, d, mode, &out);
    return rc == LK_OK ? out : rc;
}

int main(void) {
    int64_t out = 0;

    /* exact division never rounds */
    CHECK_EQ(rd(10, 5, LK_ROUND_HALF_UP), 2);
    CHECK_EQ(rd(-10, 5, LK_ROUND_UP), -2);

    /* half cases */
    CHECK_EQ(rd(5, 2, LK_ROUND_HALF_UP), 3);
    CHECK_EQ(rd(-5, 2, LK_ROUND_HALF_UP), -3);
    CHECK_EQ(rd(5, 2, LK_ROUND_HALF_EVEN), 2);
    CHECK_EQ(rd(7, 2, LK_ROUND_HALF_EVEN), 4);
    CHECK_EQ(rd(-5, 2, LK_ROUND_HALF_EVEN), -2);

    /* directed modes */
    CHECK_EQ(rd(7, 3, LK_ROUND_DOWN), 2);
    CHECK_EQ(rd(-7, 3, LK_ROUND_DOWN), -2);
    CHECK_EQ(rd(7, 3, LK_ROUND_UP), 3);
    CHECK_EQ(rd(-7, 3, LK_ROUND_UP), -3);
    CHECK_EQ(rd(7, -3, LK_ROUND_HALF_UP), -2);

    /* below and above half */
    CHECK_EQ(rd(10, 4, LK_ROUND_HALF_UP), 3);
    CHECK_EQ(rd(9, 4, LK_ROUND_HALF_UP), 2);
    CHECK_EQ(rd(11, 4, LK_ROUND_HALF_EVEN), 3);

    /* errors */
    CHECK_EQ(rd(1, 0, LK_ROUND_HALF_UP), LK_ERR_DIV_ZERO);
    CHECK_EQ(rd(1, 2, 9), LK_ERR_MODE);
    CHECK_EQ(rd(INT64_MIN, 1, LK_ROUND_DOWN), INT64_MIN);
    CHECK_EQ(lk_round_div(INT64_MIN, -1, LK_ROUND_DOWN, &out), LK_ERR_OVERFLOW);

    /* checked arithmetic */
    CHECK_EQ(lk_add_checked(INT64_MAX, 1, &out), LK_ERR_OVERFLOW);
    CHECK_EQ(lk_add_checked(INT64_MIN, -1, &out), LK_ERR_OVERFLOW);
    CHECK_EQ(lk_add_checked(INT64_MAX, -1, &out), LK_OK);
    CHECK_EQ(out, INT64_MAX - 1);
    CHECK_EQ(lk_mul_checked(INT64_MAX, 2, &out), LK_ERR_OVERFLOW);
    CHECK_EQ(lk_mul_checked(INT64_MIN, -1, &out), LK_ERR_OVERFLOW);
    CHECK_EQ(lk_mul_checked(-3037000500LL, 3037000500LL, &out), LK_ERR_OVERFLOW);
    CHECK_EQ(lk_mul_checked(-4000000000LL, -4000000000LL, &out), LK_ERR_OVERFLOW);
    CHECK_EQ(lk_mul_checked(-3000000000LL, 3000000000LL, &out), LK_OK);
    CHECK_EQ(out, -9000000000000000000LL);
    CHECK_EQ(lk_mul_checked(0, INT64_MIN, &out), LK_OK);
    CHECK_EQ(out, 0);

    CHECK_DONE();
}
