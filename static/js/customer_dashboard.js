/* =====================================================
   CUSTOMER DASHBOARD SEARCH
===================================================== */

document.addEventListener("DOMContentLoaded", function () {


    const searchInput =
        document.getElementById("customerSearch");


    const clearButton =
        document.getElementById("clearSearch");


    const searchMessage =
        document.getElementById("searchMessage");


    const productCards =
        document.querySelectorAll(".customer-product-card");


    const categoryCards =
        document.querySelectorAll(".customer-category-card");


    const noProducts =
        document.getElementById("noProducts");



    /* =================================================
       SEARCH FUNCTION
    ================================================= */

    function performSearch() {


        const searchValue =
            searchInput.value
                .trim()
                .toLowerCase();


        let visibleProducts = 0;

        let visibleCategories = 0;



        /* =============================================
           PRODUCTS
        ============================================= */

        productCards.forEach(function (card) {


            const productName =
                card.dataset.productName || "";


            const productCategory =
                card.dataset.productCategory || "";


            const productDescription =
                card.dataset.productDescription || "";


            const searchableText =
                (
                    productName +
                    " " +
                    productCategory +
                    " " +
                    productDescription
                ).toLowerCase();


            if (
                searchValue === "" ||
                searchableText.includes(searchValue)
            ) {

                card.style.display = "";

                visibleProducts++;

            } else {

                card.style.display = "none";

            }

        });



        /* =============================================
           CATEGORIES
        ============================================= */

        categoryCards.forEach(function (card) {


            const categoryName =
                card.dataset.category || "";


            if (
                searchValue === "" ||
                categoryName.includes(searchValue)
            ) {

                card.style.display = "";

                visibleCategories++;

            } else {

                card.style.display = "none";

            }

        });



        /* =============================================
           SEARCH MESSAGE
        ============================================= */

        if (searchValue === "") {

            searchMessage.textContent =
                "Showing all products";

        } else {

            searchMessage.textContent =
                "Found " +
                visibleProducts +
                " product(s) and " +
                visibleCategories +
                " categor" +
                (
                    visibleCategories === 1
                    ? "y"
                    : "ies"
                ) +
                " matching \"" +
                searchValue +
                "\"";

        }



        /* =============================================
           NO PRODUCT MESSAGE
        ============================================= */

        if (visibleProducts === 0) {

            noProducts.classList.remove("hidden");

        } else {

            noProducts.classList.add("hidden");

        }



        /* =============================================
           CLEAR BUTTON
        ============================================= */

        if (searchValue !== "") {

            clearButton.style.display =
                "block";

        } else {

            clearButton.style.display =
                "none";

        }

    }



    /* =================================================
       INPUT EVENT
    ================================================= */

    searchInput.addEventListener(
        "input",
        performSearch
    );



    /* =================================================
       CLEAR SEARCH
    ================================================= */

    clearButton.addEventListener(
        "click",
        function () {

            searchInput.value = "";

            performSearch();

            searchInput.focus();

        }
    );



    /* =================================================
       CATEGORY CLICK
    ================================================= */

    categoryCards.forEach(function (categoryCard) {


        categoryCard.addEventListener(
            "click",
            function () {


                const categoryName =
                    categoryCard.dataset.category;


                /* Highlight selected category */

                categoryCards.forEach(
                    function (card) {

                        card.classList.remove(
                            "selected"
                        );

                    }
                );


                categoryCard.classList.add(
                    "selected"
                );


                /* Put category into search */

                searchInput.value =
                    categoryName;


                performSearch();


                /* Scroll to products */

                document
                    .getElementById("products")
                    .scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });

            }
        );

    });



    /* =================================================
       WISHLIST UI
    ================================================= */

    const wishlistButtons =
        document.querySelectorAll(
            ".wishlist-button"
        );


    wishlistButtons.forEach(
        function (button) {


            button.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    event.stopPropagation();


                    if (
                        button.textContent.trim()
                        === "♡"
                    ) {

                        button.textContent = "♥";

                        button.style.color =
                            "#ef946d";

                    } else {

                        button.textContent = "♡";

                        button.style.color =
                            "#777777";

                    }

                }
            );

        }
    );



    /* =================================================
       ADD TO CART UI
    ================================================= */

    const cartButtons =
        document.querySelectorAll(
            ".add-cart-button"
        );


    cartButtons.forEach(
        function (button) {


            button.addEventListener(
                "click",
                function () {


                    if (button.disabled) {

                        return;

                    }


                    const originalText =
                        button.textContent;


                    button.textContent =
                        "Added ✓";


                    button.style.background =
                        "#4da8c5";


                    setTimeout(
                        function () {

                            button.textContent =
                                originalText;

                            button.style.background =
                                "";

                        },
                        1200
                    );

                }
            );

        }
    );


});