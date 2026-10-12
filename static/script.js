document.addEventListener(
    "DOMContentLoaded",
    function () {


        // =====================================================
        // FARMING METHOD SELECTION
        // =====================================================

        const methodCards =
            document.querySelectorAll(
                ".method-card"
            );

        const selectedMethod =
            document.getElementById(
                "selected-method"
            );

        const registerMethod =
            document.getElementById(
                "register-method"
            );


        function selectMethod(method) {

            if (selectedMethod) {

                selectedMethod.textContent =
                    method;

            }


            if (registerMethod) {

                registerMethod.value =
                    method;

            }


            methodCards.forEach(
                function (card) {

                    if (
                        card.dataset.method ===
                        method
                    ) {

                        card.classList.add(
                            "selected"
                        );

                    } else {

                        card.classList.remove(
                            "selected"
                        );

                    }

                }
            );

        }


        methodCards.forEach(
            function (card) {

                card.addEventListener(
                    "click",
                    function () {

                        selectMethod(
                            card.dataset.method
                        );


                        const authBox =
                            document.getElementById(
                                "auth-box"
                            );


                        if (authBox) {

                            authBox.scrollIntoView({
                                behavior: "smooth",
                                block: "center"
                            });

                        }

                    }
                );

            }
        );


        // Default selection

        if (methodCards.length > 0) {

            selectMethod(
                "Open Field"
            );

        }



        // =====================================================
        // REGISTER / LOGIN TABS
        // =====================================================

        const authTabs =
            document.querySelectorAll(
                ".auth-tab"
            );

        const registerForm =
            document.getElementById(
                "register-form"
            );

        const loginForm =
            document.getElementById(
                "login-form"
            );


        authTabs.forEach(
            function (tab) {

                tab.addEventListener(
                    "click",
                    function () {


                        authTabs.forEach(
                            function (item) {

                                item.classList.remove(
                                    "active"
                                );

                            }
                        );


                        tab.classList.add(
                            "active"
                        );


                        if (
                            tab.dataset.tab ===
                            "register"
                        ) {

                            registerForm.classList.remove(
                                "hidden"
                            );

                            loginForm.classList.add(
                                "hidden"
                            );

                        } else {

                            registerForm.classList.add(
                                "hidden"
                            );

                            loginForm.classList.remove(
                                "hidden"
                            );

                        }

                    }
                );

            }
        );



        // =====================================================
        // ADD FARM FORM
        // =====================================================

        const farmForm =
            document.getElementById(
                "farm-form-box"
            );


        const showFarmButton =
            document.getElementById(
                "show-farm-form"
            );


        const emptyAddButton =
            document.getElementById(
                "empty-add-farm"
            );


        const closeFormButton =
            document.getElementById(
                "close-form"
            );


        function showFarmForm() {

            if (!farmForm) {
                return;
            }


            farmForm.classList.remove(
                "hidden"
            );


            farmForm.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

        }


        if (showFarmButton) {

            showFarmButton.addEventListener(
                "click",
                showFarmForm
            );

        }


        if (emptyAddButton) {

            emptyAddButton.addEventListener(
                "click",
                showFarmForm
            );

        }


        if (closeFormButton) {

            closeFormButton.addEventListener(
                "click",
                function () {

                    farmForm.classList.add(
                        "hidden"
                    );

                }
            );

        }



        // =====================================================
        // EDIT / DELETE FARM
        // =====================================================

        const editFarmBox =
            document.getElementById("edit-farm-form-box");

        const editFarmForm =
            document.getElementById("edit-farm-form");

        const closeEditFormButton =
            document.getElementById("close-edit-form");

        const editFarmButtons =
            document.querySelectorAll(".edit-farm-button");

        function openEditFarmForm(button) {
            if (!editFarmBox || !editFarmForm) return;

            const farmId = button.dataset.farmId;

            editFarmForm.action = "/farms/" + farmId + "/edit";
            document.getElementById("edit-farm-name").value = button.dataset.farmName;
            document.getElementById("edit-farm-method").value = button.dataset.method;
            document.getElementById("edit-farm-location").value = button.dataset.location;
            document.getElementById("edit-farm-crop").value = button.dataset.crop;
            document.getElementById("edit-farm-growth-stage").value = button.dataset.growthStage;
            document.getElementById("edit-farm-threshold").value = button.dataset.threshold;

            editFarmBox.classList.remove("hidden");
            editFarmBox.scrollIntoView({ behavior: "smooth", block: "center" });
        }

        editFarmButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                openEditFarmForm(button);
            });
        });

        if (closeEditFormButton) {
            closeEditFormButton.addEventListener("click", function () {
                editFarmBox.classList.add("hidden");
            });
        }

        document.querySelectorAll(".delete-farm-form").forEach(function (form) {
            form.addEventListener("submit", function (event) {
                const confirmed = window.confirm(
                    "Delete this farm? Its alert history will also be deleted."
                );

                if (!confirmed) {
                    event.preventDefault();
                }
            });
        });


        // =====================================================
        // WEATHER CHECK
        // =====================================================

        const weatherButtons =
            document.querySelectorAll(
                ".weather-button"
            );


        weatherButtons.forEach(
            function (button) {


                button.addEventListener(
                    "click",
                    async function () {


                        const farmId =
                            button.dataset.farmId;


                        const resultBox =
                            document.getElementById(
                                "weather-" +
                                farmId
                            );


                        button.disabled = true;

                        button.textContent =
                            "Checking weather...";


                        resultBox.classList.remove(
                            "hidden"
                        );


                        resultBox.classList.remove(
                            "safe",
                            "risk"
                        );


                        resultBox.innerHTML =
                            "🌤️ Getting weather information...";


                        try {


                            const response =
                                await fetch(
                                    "/weather/" +
                                    farmId,
                                    {
                                        method: "POST"
                                    }
                                );


                            const data =
                                await response.json();


                            if (!response.ok ||
                                !data.success) {

                                throw new Error(
                                    data.message ||
                                    "Weather check failed."
                                );

                            }


                            // ------------------------------------------------
                            // SAFE
                            // ------------------------------------------------

                            if (!data.alert.triggered) {

                                resultBox.classList.add(
                                    "safe"
                                );


                                resultBox.innerHTML = `

                                    <strong>
                                        ✓ Temperature is within safe limit
                                    </strong>

                                    <div class="weather-values">

                                        <div>

                                            <strong>
                                                ${Number(
                                    data.weather.temperature
                                ).toFixed(1)}°C
                                            </strong>

                                            Current

                                        </div>


                                        <div>

                                            <strong>
                                                ${false
                                        ? Number(
                                            data.forecast_max
                                        ).toFixed(1) + "°C"
                                        : "N/A"}
                                            </strong>

                                            Forecast Max

                                        </div>


                                        <div>

                                            <strong>
                                                ${data.weather.humidity !== null && data.weather.humidity !== undefined
                                        ? data.weather.humidity + "%"
                                        : "N/A"}
                                            </strong>

                                            Humidity

                                        </div>

                                    </div>

                                    📍 ${escapeHTML(
                                            ([data.location.name, data.location.state, data.location.country].filter(Boolean).join(", "))
                                        )}

                                `;

                            }


                            // ------------------------------------------------
                            // HEAT RISK
                            // ------------------------------------------------

                            else {

                                resultBox.classList.add(
                                    "risk"
                                );


                                resultBox.innerHTML = `

                                    <strong>
                                        ⚠️ Extreme Heat Alert!
                                    </strong>

                                    <div class="weather-values">

                                        <div>

                                            <strong>
                                                ${Number(
                                    data.weather.temperature
                                ).toFixed(1)}°C
                                            </strong>

                                            Current

                                        </div>


                                        <div>

                                            <strong>
                                                ${false
                                        ? Number(
                                            data.forecast_max
                                        ).toFixed(1) + "°C"
                                        : "N/A"}
                                            </strong>

                                            Forecast Max

                                        </div>


                                        <div>

                                            <strong>
                                                ${data.weather.humidity !== null && data.weather.humidity !== undefined
                                        ? data.weather.humidity + "%"
                                        : "N/A"}
                                            </strong>

                                            Humidity

                                        </div>

                                    </div>


                                    📍 ${escapeHTML(
                                            ([data.location.name, data.location.state, data.location.country].filter(Boolean).join(", "))
                                        )}


                                    <p>

                                        ${escapeHTML(
                                            data.alert.message ||
                                            "Heat alert generated."
                                        )}

                                    </p>

                                `;

                            }


                        } catch (error) {


                            resultBox.classList.add(
                                "risk"
                            );


                            resultBox.innerHTML = `

                                ❌
                                ${escapeHTML(
                                error.message
                            )}

                            `;


                        }


                        finally {

                            button.disabled =
                                false;

                            button.textContent =
                                "Check Weather →";

                        }

                    }
                );

            }
        );



        // =====================================================
        // SECURITY HELPER
        // =====================================================

        function escapeHTML(value) {

            return String(value).replace(
                /[&<>"']/g,
                function (character) {

                    const characters = {

                        "&": "&amp;",
                        "<": "&lt;",
                        ">": "&gt;",
                        '"': "&quot;",
                        "'": "&#039;"

                    };

                    return characters[
                        character
                    ];

                }
            );

        }

    }
);