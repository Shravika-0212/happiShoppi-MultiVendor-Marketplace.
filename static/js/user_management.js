const searchInput = document.getElementById('userSearch');

const tableBody = document.getElementById('usersTableBody');

const noResults = document.getElementById('noResults');


searchInput.addEventListener('input', function () {

    const searchValue = searchInput.value
        .toLowerCase()
        .trim();

    const rows = tableBody.getElementsByTagName('tr');

    let visibleRows = 0;


    for (let i = 0; i < rows.length; i++) {

        const rowText = rows[i].textContent.toLowerCase();

        if (rowText.includes(searchValue)) {

            rows[i].style.display = '';

            visibleRows++;

        } else {

            rows[i].style.display = 'none';

        }

    }


    if (visibleRows === 0) {

        noResults.style.display = 'block';

    } else {

        noResults.style.display = 'none';

    }

});