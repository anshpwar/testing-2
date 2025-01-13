#include <string.h>

#include "check.h"
#include "lk_iban.h"

int main(void) {
    lk_iban_info info;
    char digits[3];

    CHECK_EQ(lk_iban_info_sizeof(), sizeof(lk_iban_info));
    CHECK_EQ(lk_iban_info_sizeof(), 16);

    /* well-known documentation IBANs */
    CHECK_EQ(lk_iban_validate("DE89370400440532013000"), LK_OK);
    CHECK_EQ(lk_iban_validate("GB82WEST12345698765432"), LK_OK);
    CHECK_EQ(lk_iban_validate("FR1420041010050500013M02606"), LK_OK);
    CHECK_EQ(lk_iban_validate("NL91ABNA0417164300"), LK_OK);
    CHECK_EQ(lk_iban_validate("ES9121000418450200051332"), LK_OK);

    /* remainder is 1 for valid numbers */
    CHECK_EQ(lk_iban_mod97("DE89370400440532013000"), 1);
    CHECK(lk_iban_mod97("DE88370400440532013000") != 1);

    /* failures are classified */
    CHECK_EQ(lk_iban_validate("DE88370400440532013000"), LK_ERR_IBAN_CHECK);
    CHECK_EQ(lk_iban_validate("DE8937040044053201300"), LK_ERR_IBAN_LENGTH);
    CHECK_EQ(lk_iban_validate("XX89370400440532013000"), LK_ERR_IBAN_COUNTRY);
    CHECK_EQ(lk_iban_validate("de89370400440532013000"), LK_ERR_IBAN_FORMAT);
    CHECK_EQ(lk_iban_validate("DEAB370400440532013000"), LK_ERR_IBAN_FORMAT);
    CHECK_EQ(lk_iban_validate("DE"), LK_ERR_IBAN_LENGTH);
    CHECK_EQ(lk_iban_validate(NULL), LK_ERR_ARG);

    /* check digit generation round-trips */
    CHECK_EQ(lk_iban_check_digits("DE", "370400440532013000", digits), LK_OK);
    CHECK(strcmp(digits, "89") == 0);
    CHECK_EQ(lk_iban_check_digits("GB", "WEST12345698765432", digits), LK_OK);
    CHECK(strcmp(digits, "82") == 0);
    CHECK_EQ(lk_iban_check_digits("DE", "37040044053201300!", digits), LK_ERR_IBAN_FORMAT);
    CHECK_EQ(lk_iban_check_digits("D", "37", digits), LK_ERR_IBAN_FORMAT);

    /* lengths */
    CHECK_EQ(lk_iban_expected_length("DE"), 22);
    CHECK_EQ(lk_iban_expected_length("NL"), 18);
    CHECK_EQ(lk_iban_expected_length("ZZ"), LK_ERR_IBAN_COUNTRY);

    /* parse */
    CHECK_EQ(lk_iban_parse("NL91ABNA0417164300", &info), LK_OK);
    CHECK(strcmp(info.country, "NL") == 0);
    CHECK_EQ(info.check_digits, 91);
    CHECK_EQ(info.length, 18);
    CHECK_EQ(info.expected_length, 18);
    CHECK_EQ(lk_iban_parse("NL00ABNA0417164300", &info), LK_ERR_IBAN_CHECK);

    CHECK_DONE();
}
