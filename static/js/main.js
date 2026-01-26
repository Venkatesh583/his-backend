function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    fetch("/cw-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.id) {
            alert("Login successful! Welcome " + data.name);
            window.location.href = "/dashboard";
        } else {
            alert(data.message);
        }
    })
    .catch(err => console.error(err));
}
