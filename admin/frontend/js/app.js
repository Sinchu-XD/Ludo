const API = "http://localhost:8000";
let TOKEN = localStorage.getItem("token");

function login() {
  fetch(API + "/login", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      username: document.getElementById("username").value,
      password: document.getElementById("password").value
    })
  })
  .then(r => r.json())
  .then(d => {
    if (d.access_token) {
      localStorage.setItem("token", d.access_token);
      window.location = "dashboard.html";
    } else {
      document.getElementById("msg").innerText = "Login failed";
    }
  });
}

function authHeaders() {
  return {
    "Authorization": "Bearer " + localStorage.getItem("token")
  };
}

function loadDashboard() {
  fetch(API + "/stats", {headers: authHeaders()})
    .then(r => r.json())
    .then(d => {
      document.getElementById("stats").innerText =
        JSON.stringify(d, null, 2);
    });
}

function searchUser() {
  const uid = document.getElementById("uid").value;
  fetch(API + "/users/search?user_id=" + uid, {
    headers: authHeaders()
  })
  .then(r => r.json())
  .then(d => {
    document.getElementById("users").innerText =
      JSON.stringify(d, null, 2);
  });
}

function loadGames() {
  fetch(API + "/games/active", {
    headers: authHeaders()
  })
  .then(r => r.json())
  .then(d => {
    document.getElementById("games").innerText =
      JSON.stringify(d, null, 2);
  });
}

