// Select the previous set "category" of the select HTML element in ADD and
// EDIT pages
const selectCategory = value => {
    if (value != "None") {
        let element = document.getElementById("category");
        element.value = value;
    }
};
