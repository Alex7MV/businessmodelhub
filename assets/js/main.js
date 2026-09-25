(function () {
    var link = document.querySelector(".footer-email");
    if (!link) return;
    link.addEventListener("click", function (event) {
        event.preventDefault();
        var reversed = link.querySelector(".rev").textContent.trim();
        window.location.href = "mailto:" + reversed.split("").reverse().join("");
    });
})();
