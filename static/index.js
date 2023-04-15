"use strict";

function downloadFromBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
}

const sleep = (mill) => new Promise((resolve) => setTimeout(resolve, mill));

async function startSpinnerCounter() {
    const spinner = document.getElementById("spinner-text");
    const loadingContainer = document.getElementById("loading");
    const counter = 30.0;
    const tic = Date.now();

    while (true) {
        if (loadingContainer.style.display === "none") {
            break;
        }
        const step = counter - (Date.now() - tic) / 1000;
        if (step <= 0) {
            spinner.innerText = "0";
            break;
        }
        spinner.innerText = step.toFixed(1);
        await sleep(100);
    }
}

let chosenSeriesId = null;
let updateCookieRef = null;
const GENRIC_LOGIN_ERROR = "Unknown error accured while trying to login to sdarot.tv";

async function downloadVideo() {
   if (!chosenSeriesId) {
        alert("Please choose a series from the list");
        return;
    }

    await updateCookieRef;
    const cookie = localStorage.getItem("sdarotTVCookie");
    if (!cookie) {
        alert("Please login first to sdaort.tv");
        return;
    }

    const errorContainer = document.getElementById("error");
    errorContainer.innerHTML = "";
    errorContainer.classList.remove("error");

    const loadingContainer = document.getElementById("loading");
    loadingContainer.style.display = "block";

    startSpinnerCounter();

    const name = document.querySelector("[name=series-name]").value;
    const season = document.querySelector("[name=season]").value;
    const episode = document.querySelector("[name=episode]").value;

    const loadingText = document.getElementById("loading-text");
    loadingText.innerHTML = `Loading season ${season} episode ${episode} of <br/> "${name}"`;

    const downloadBtn = document.getElementById("download-btn");
    downloadBtn.disabled = true;
    downloadBtn.innerText = "Downloading...";

    try {
        const res = await fetch("/download", {
            method: "POST", headers: {
                "Content-Type": "application/json"
            }, body: JSON.stringify({
                cookie,
                name,
                seriesId: chosenSeriesId,
                season,
                episode
            })
        });
        if (res.status === 200) {
            const blob = await res.blob();
            downloadFromBlob(blob, `${name} - S${season}E${episode}.mp4`);
        } else {
            const data = await res.json().catch(() => ({}));
            const error = data.error || "Unknown error accured while trying to download the episode";
            errorContainer.innerHTML = error;
            errorContainer.classList.add("error");
        }
    } finally {
        loadingContainer.style.display = "none";
        loadingText.innerHTML = "";
        downloadBtn.innerText = "Download";
        downloadBtn.disabled = false;
    }

}

const getLoginBtn = () => document.getElementById("login-btn");

function fillInputs() {
    const username = localStorage.getItem("username");
    const password = localStorage.getItem("password");
    const userInput = document.querySelector("[name=username]");
    const passwordInput = document.querySelector("[name=password]");

    userInput.value = username;
    passwordInput.value = password;

    return [userInput, passwordInput];
}

function changeLoginModalMode(mode) {
    if (mode === "edit") {
        const userInput = document.querySelector("[name=username]");
        const passwordInput = document.querySelector("[name=password]");

        userInput.disabled = false;
        passwordInput.disabled = false;

        getLoginBtn().innerText = "Login to sdaort.tv";
    } else if (mode === "saved") {
        const [userInput, passwordInput] = fillInputs();

        userInput.disabled = true;
        passwordInput.disabled = true;

        getLoginBtn().innerText = "Logout";
    }
}

async function login() {
    const loginBtn = getLoginBtn();
    if (loginBtn.innerText === "Logout") {
        localStorage.removeItem("username");
        localStorage.removeItem("password");
        localStorage.removeItem("sdarotTVCookie");
        changeLoginModalMode("edit");
        return;
    }

    loginBtn.disabled = true;
    loginBtn.innerText = "Logging in...";
    const username = document.querySelector("[name=username]").value;
    const password = document.querySelector("[name=password]").value;

    const revertLoginBtn = () => {
        loginBtn.disabled = false;
        loginBtn.innerText = "Login to sdaort.tv";
    }

    try {
        const res = await fetch("/login", {
            method: "POST", headers: {
                "Content-Type": "application/json"
            }, body: JSON.stringify({
                username,
                password
            })
        });

        const data = await res.json();
        if (!data.sdarotTVCookie) {
            revertLoginBtn();
            alert(data.error || GENRIC_LOGIN_ERROR);
            return;
        }

        localStorage.setItem("username", username);
        localStorage.setItem("password", password);
        localStorage.setItem("sdarotTVCookie", data.sdarotTVCookie);

        changeLoginModalMode("saved");
        alert("Logged in successfully");

        loginBtn.disabled = false;
    } catch (e) {
        revertLoginBtn();
        alert(GENRIC_LOGIN_ERROR);
    }
}

async function updateCookie() {
    const username = localStorage.getItem("username");
    const password = localStorage.getItem("password");
    if (!username || !password) {
        localStorage.setItem("sdarotTVCookie", "");
        alert("Tried to update cookie but no username or password was found")
        return;
    }

    try {
        const res = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username,
                password
            })
        });

        const data = await res.json();
        if (!data.sdarotTVCookie) {
            changeLoginModalMode("edit");
            localStorage.setItem("sdarotTVCookie", "");
            alert(data.error || GENRIC_LOGIN_ERROR);
            return;
        }

        localStorage.setItem("sdarotTVCookie", data.sdarotTVCookie);
        return data.sdarotTVCookie;
    } catch (e) {
        localStorage.setItem("sdarotTVCookie", "");
        alert(GENRIC_LOGIN_ERROR);
    }
}

async function search(seriesName) {
    const res = await fetch("/search", {
        method: "POST", headers: {
            "Content-Type": "application/json"
        }, body: JSON.stringify({
            name: seriesName,
            cookie: ""
        })
    });
    return await res.json();
}

function onStart() {
    const sdarotTVCookie = localStorage.getItem("sdarotTVCookie");
    if (sdarotTVCookie) {
        changeLoginModalMode("saved");
        updateCookieRef = updateCookie();
    } else {
        changeLoginModalMode("edit");
    }

    autocomplete(document.querySelector("[name=series-name]"));

    document.getElementById("login-form").addEventListener("submit", (e) => {
        e.preventDefault();
        login();
    });

    document.getElementById("download-form").addEventListener("submit", (e) => {
        e.preventDefault();
        downloadVideo();
    });
}

async function onSeriesChosen(seriesId) {
     const response = await fetch("/series", {
        method: "POST", headers: {
            "Content-Type": "application/json"
        }, body: JSON.stringify({
            seriesId: seriesId,
            season: 1,
        })
    });
    const res = await response.json();
    if (response.status !== 200) {
        alert(res.error || "Failed to get series info from sdaort.tv");
        return;
    }

    const selectSeason = document.querySelector("[name=season]");
    const selectEpisode = document.querySelector("[name=episode]");

    selectSeason.innerHTML = "";
    for (let season of res.seasons) {
        const option = document.createElement("option");
        option.value = season;
        option.innerText = season;
        selectSeason.appendChild(option);
    }

    selectEpisode.innerHTML = "";
    for (let episode of res.episodes) {
        const option = document.createElement("option");
        option.value = episode;
        option.innerText = episode;
        document.querySelector("[name=episode]").appendChild(option);
        selectEpisode.appendChild(option);
    }

    selectSeason.disabled = false;
    selectEpisode.disabled = false;
}

async function onSeasonChosen() {
    const season = document.querySelector("[name=season]").value;
    const response = await fetch("/episodes", {
        method: "POST", headers: {
            "Content-Type": "application/json"
        }, body: JSON.stringify({
            seriesId: chosenSeriesId,
            season: season,
        })
    });
    const res = await response.json();
    if (response.status !== 200) {
        alert(res.error || "Failed to get series info from sdaort.tv");
        return;
    }

    const selectEpisode = document.querySelector("[name=episode]");
    selectEpisode.innerHTML = "";
    for (let episode of res.episodes) {
        const option = document.createElement("option");
        option.value = episode;
        option.innerText = episode;
        selectEpisode.appendChild(option);
    }
}

function autocomplete(inp) {
    var currentFocus;

    let arr = [];
    let lastSearch = Date.now();

    const delaySearch = (fn, delay, currentSearch) => {
        setTimeout(() => {
            if (currentSearch === lastSearch) {
                fn();
            }
        }, delay);
    };

    async function onInput(e, force) {
        const ths = document.querySelector("[name=series-name]");
        var a, b, i, val = ths.value;
        closeAllLists();
        if (!val || val.length < 3) {
            return false;
        }
        currentFocus = -1;
        a = document.createElement("DIV");
        a.setAttribute("id", ths.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        ths.parentNode.appendChild(a);

        const now = Date.now();
        if (now - lastSearch < 500 && !force) {
            delaySearch(() => onInput(e, true), 1000 - (now - lastSearch), now);
            lastSearch = now;
            return;
        }

        lastSearch = now;

        arr = await search(val);

        for (i = 0; i < arr.length; i++) {
            b = document.createElement("DIV");
            b.innerHTML = "<strong>" + arr[i].name.substr(0, val.length) + "</strong>";
            b.innerHTML += arr[i].name.substr(val.length);
            b.innerHTML += `<input type='hidden' value='${arr[i].name}' seris-id='${arr[i].id}'>`;
            b.addEventListener("click", function (e) {
                const chosenInp = this.getElementsByTagName("input")[0];
                inp.value = chosenInp.value;
                chosenSeriesId = chosenInp.getAttribute("seris-id");
                closeAllLists();
                onSeriesChosen(chosenSeriesId);
            });
            a.appendChild(b);
        }
    }

    inp.addEventListener("input", onInput);

    inp.addEventListener("keydown", function (e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            currentFocus++;
            addActive(x);
        } else if (e.keyCode == 38) { //up
            currentFocus--;
            addActive(x);
        } else if (e.keyCode == 13) {
            e.preventDefault();
            if (currentFocus > -1) {
                if (x) x[currentFocus].click();
            }
        }
    });

    function addActive(x) {
        if (!x) return false;
        removeActive(x);
        if (currentFocus >= x.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (x.length - 1);
        x[currentFocus].classList.add("autocomplete-active");
    }

    function removeActive(x) {
        for (var i = 0; i < x.length; i++) {
            x[i].classList.remove("autocomplete-active");
        }
    }

    function closeAllLists(elmnt) {
        var x = document.getElementsByClassName("autocomplete-items");
        for (var i = 0; i < x.length; i++) {
            if (elmnt != x[i] && elmnt != inp) {
                x[i].parentNode.removeChild(x[i]);
            }
        }
    }

    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });

}

onStart();
