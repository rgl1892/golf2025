document.addEventListener("DOMContentLoaded", () => {
    const playerContainer = document.getElementById("playerContainer");

    for (let i = 1; i <= 4; i++) {
        playerContainer.innerHTML += `
            <div class="mb-3">
                <label for="player_${i}" class="form-label" id="label_player_${i}">Player ${i}:</label>
                <div class="d-flex flex-column flex-sm-row align-items-center">
                    <select id="player_${i}" class="form-select form-select-player mb-2 mb-sm-0 me-sm-2 w-100 w-sm-auto" name="player_${i}">
                        <option value="">--Select a Player--</option>
                    </select>
                    <input type="number" id="player_${i}_index" class="form-control w-100 w-sm-auto" step="0.1" placeholder="Index" name="player_${i}_index">
                </div>
            </div>
        `;
    };

    const courseData = JSON.parse(document.querySelector('#courseJsonData').dataset.json);
    const playerData = JSON.parse(document.querySelector('#playerJsonData').dataset.json);

    const countrySelect = document.getElementById("countrySelect");
    const courseSelect = document.getElementById("courseSelect");
    const teeSelect = document.getElementById("teeSelect");
    const slopeReturn = document.getElementById("slopeReturn");
    const parReturn = document.getElementById("parReturn");
    const strokeReturn = document.getElementById("strokeReturn");
    
    const playerSelects = document.querySelectorAll(".form-select-player");

    const populateSelect = (select, options, defaultText) => {
        select.innerHTML = `<option value="">${defaultText}</option>`;
        options.forEach(optionValue => {
            console.log(optionValue);
            const option = document.createElement("option");
            option.value = optionValue;
            option.textContent = optionValue;
            select.appendChild(option);
        });
        select.disabled = options.length === 0;
    };

    const populateCountries = () => {
        const countries = [...new Set(courseData.map(course => course.country))];
        populateSelect(countrySelect, countries, "--Select a Country--");
    };

    const populateCourses = () => {
        const selectedCountry = countrySelect.value;
        const courses = [...new Set(
            courseData.filter(course => course.country === selectedCountry).map(course => course.name)
        )];
        populateSelect(courseSelect, courses, "--Select a Course--");
        populateSelect(teeSelect, [], "--Select a Tee--"); // Reset tees
    };

    const populateTees = () => {
        const selectedCountry = countrySelect.value;
        const selectedCourse = courseSelect.value;
        const tees = [...new Set(
            courseData.filter(course => course.country === selectedCountry && course.name === selectedCourse)
                    .map(course => course.tees)
        )];
        populateSelect(teeSelect, tees, "--Select a Tee--");
    };

    const displayCourseInfo = () => {
        const selectedCountry = countrySelect.value;
        const selectedCourse = courseSelect.value;
        const selectedTee = teeSelect.value;
        const courseInput = document.getElementById('courseId');

        
        const chosenCourse = courseData.find(course => 
            course.country === selectedCountry && 
            course.name === selectedCourse && 
            course.tees === selectedTee
        );
        
        if (chosenCourse) {
            slopeReturn.textContent = `Slope: ${chosenCourse.slope_rating}`;
            parReturn.textContent = `Par: ${chosenCourse.par}`;
            strokeReturn.textContent = `Stroke: ${chosenCourse.course_rating}`;
            courseInput.value = chosenCourse.id;
            return {
                slope: chosenCourse.slope_rating,
                par: chosenCourse.par,
                course: chosenCourse.course_rating
            };
        }
        return null;
    };

    const getHandicap = (index, courseInfo) => 
        ((parseFloat(courseInfo.slope_rating) / 113) * index + parseFloat(courseInfo.course_rating) - parseFloat(courseInfo.par)).toFixed(0);

    const populatePlayerSelects = () => {
        const selectedPlayers = new Set([...playerSelects].map(select => select.value).filter(Boolean));

        playerSelects.forEach(select => {
            const currentSelection = select.value;
            select.innerHTML = '<option value="">--Select a Player--</option>';

            playerData.forEach(player => {
                const playerId = player.id.toString();
                if (!selectedPlayers.has(playerId) || playerId === currentSelection) {
                    const option = document.createElement("option");
                    option.value = playerId;
                    option.textContent = `${player.first_name} ${player.second_name}`;
                    select.appendChild(option);
                }
            });
            select.value = currentSelection;
        });
    };

    /**
     * Updates the player label with the index value when typed.
     */
    const updatePlayerIndexLabel = (playerIndex) => {
        const indexInput = document.getElementById(`player_${playerIndex}_index`);
        const label = document.getElementById(`label_player_${playerIndex}`);
        const indexValue =  parseFloat(indexInput.value);

        const selectedCountry = countrySelect.value;
        const selectedCourse = courseSelect.value;
        const selectedTee = teeSelect.value;
        const chosenCourse = courseData.find(course => 
            course.country === selectedCountry && 
            course.name === selectedCourse && 
            course.tees === selectedTee
        );
        if (!chosenCourse){
            console.error("Chosen course not found:", selectedCountry, selectedCourse, selectedTee);
        }
        const handicap = getHandicap(indexValue,chosenCourse) 

        if (indexValue) {
            label.textContent = `Player ${playerIndex}: (Handicap: ${handicap})`;
        } else {
            label.textContent = `Player ${playerIndex}:`;
        }
    };

    // Event listeners for player index input to update the label
    for (let i = 1; i <= 4; i++) {
        const indexInput = document.getElementById(`player_${i}_index`);
        indexInput.addEventListener("input", () => updatePlayerIndexLabel(i));
    }

    // Event listeners
    countrySelect.addEventListener("change", populateCourses);
    courseSelect.addEventListener("change", populateTees);
    teeSelect.addEventListener("change", displayCourseInfo);
    teeSelect.addEventListener("change", populatePlayerSelects);
    playerSelects.forEach(select => select.addEventListener("change", populatePlayerSelects));

    // Initial population
    populateCountries();
    
});
