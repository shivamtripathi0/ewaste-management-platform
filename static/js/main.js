function applyFilters() {
    const filter = document.getElementById("filterSelect").value;
    const sort = document.getElementById("sortSelect").value;
    window.location.href = `/buy?filter=${filter}&sort=${sort}`;
}

function searchItems() {
    let query = document.getElementById("searchInput").value;
    console.log("Searching:", query);
}