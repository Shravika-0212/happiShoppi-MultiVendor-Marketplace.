/* =====================================================
   HOME PAGE SEARCH
===================================================== */

document.addEventListener("DOMContentLoaded", function () {

    const searchForm = document.querySelector(".search-form");
    const searchInput = document.querySelector(".search-form input");

    const productCards = document.querySelectorAll(".product-card");
    const categoryCards = document.querySelectorAll(".category-card");


    /* =================================================
       SEARCH FUNCTION
    ================================================= */

    function performSearch() {

        const searchText = searchInput.value.trim().toLowerCase();


        /* =============================================
           IF SEARCH IS EMPTY
        ============================================= */

        if (searchText === "") {

            productCards.forEach(function (card) {
                card.style.display = "";
            });

            categoryCards.forEach(function (card) {
                card.style.display = "";
            });

            return;
        }


        /* =============================================
           SEARCH PRODUCTS
        ============================================= */

        productCards.forEach(function (card) {

            const productName =
                card.querySelector("h3")?.textContent.toLowerCase() || "";

            const productCategory =
                card.querySelector(".product-category")?.textContent.toLowerCase() || "";

            const productDescription =
                card.querySelector(".product-description")?.textContent.toLowerCase() || "";


            /*
             * Search in:
             * Product Name
             * Category
             * Description
             */

            const searchableText =
                productName + " " +
                productCategory + " " +
                productDescription;


            if (searchableText.includes(searchText)) {

                card.style.display = "";

            } else {

                card.style.display = "none";

            }

        });


        /* =============================================
           SEARCH CATEGORIES
        ============================================= */

        categoryCards.forEach(function (card) {

            const categoryName =
                card.querySelector("h3")?.textContent.toLowerCase() || "";

            const categoryDescription =
                card.querySelector("p")?.textContent.toLowerCase() || "";


            const searchableText =
                categoryName + " " +
                categoryDescription;


            if (searchableText.includes(searchText)) {

                card.style.display = "";

            } else {

                card.style.display = "none";

            }

        });

    }


    /* =================================================
       SEARCH WHILE TYPING
    ================================================= */

    searchInput.addEventListener("input", function () {

        performSearch();

    });


    /* =================================================
       PREVENT DJANGO SEARCH
    ================================================= */

    searchForm.addEventListener("submit", function (event) {

        event.preventDefault();

        performSearch();

    });

});