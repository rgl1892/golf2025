function loadJson(selector) {
    return JSON.parse(document.querySelector(selector).getAttribute('data-json'));
  }

window.onload = function () {

    const golfData = loadJson('#jsonData');

    const countrySelect = document.getElementById("countrySelect");
    const courseSelect = document.getElementById("courseSelect");
    const teeSelect = document.getElementById("teeSelect");
    
    function populateCountries() {
        const countries = [...new Set(golfData.map(course => course.country))];
        countries.forEach(country => {
            const option = document.createElement("option");
            option.value = country;
            option.textContent = country;
            countrySelect.appendChild(option);
        });
    }
    
    function populateCourses() {
        const selectedCountry = countrySelect.value;
        courseSelect.innerHTML = '<option value="">--Select a Course--</option>';
        teeSelect.innerHTML = '<option value="">--Select a Tee--</option>';
        teeSelect.disabled = true;
        
        if (!selectedCountry) {
            courseSelect.disabled = true;
            return;
        }
        
        const filteredCourses = [...new Set(golfData
            .filter(course => course.country === selectedCountry)
            .map(course => course.name))];
        
        filteredCourses.forEach(course => {
            const option = document.createElement("option");
            option.value = course;
            option.textContent = course;
            courseSelect.appendChild(option);
        });
        courseSelect.disabled = false;
    }
    
    function populateTees() {
        const selectedCountry = countrySelect.value;
        const selectedCourse = courseSelect.value;
        teeSelect.innerHTML = '<option value="">--Select a Tee--</option>';
        
        if (!selectedCourse) {
            teeSelect.disabled = true;
            return;
        }
        
        const filteredTees = [...new Set(golfData
            .filter(course => course.country === selectedCountry && course.name === selectedCourse)
            .map(course => course.tees))];
        
        filteredTees.forEach(tee => {
            const option = document.createElement("option");
            option.value = tee;
            option.textContent = tee;
            teeSelect.appendChild(option);
        });
        teeSelect.disabled = false;
    }

    function getSlope(){
        const selectedCountry = countrySelect.value;
        const selectedCourse = courseSelect.value;
        const selectedTee = teeSelect.value
        

        const chosenCourse = [...new Set(golfData
            .filter(course => course.country === selectedCountry && course.name === selectedCourse && course.tees == selectedTee))
            ][0];
        console.log(chosenCourse.slope_rating)
    }
    
    countrySelect.addEventListener("change", populateCourses);
    courseSelect.addEventListener("change", populateTees);
    teeSelect.addEventListener("change",getSlope);
    
    populateCountries();
}
