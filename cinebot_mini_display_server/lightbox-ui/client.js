
const host = "http://192.168.2.105:8088";
const hostApi = `${host}/api`;

var loginFieldIds = [
	"screenid",
	"wPx",
	"hPx",
	"ppcm",
	"wCm"
];
var loginVals = {};
var eventSource = null;

var imgElem = null;
var colorBGElem = document.getElementById("color_bg");

var tempElem = document.createElement("div");
tempElem.style.width = "1cm";
tempElem.style.height = "1cm";
document.body.insertBefore(tempElem, document.body.childNodes[0]);
rect = tempElem.getBoundingClientRect()

var ppcm = tempElem.getBoundingClientRect()["width"]

document.body.removeChild(document.body.childNodes[0]);

function login() {
	loginFieldIds.forEach((id) => {
		if (id === "wPx" || id === "hPx" || id === "ppcm" || id == "wCm") {
			var elem = document.getElementById(id);
			loginVals[id] = parseFloat(elem.value);	
		}
		else {
			var elem = document.getElementById(id);
			loginVals[id] = elem.value;
		}
	});

	var requestParams = {
		"body": JSON.stringify(loginVals),
		method: "POST"
	};
	
	fetch(`${host}/api/login`, requestParams).then((data) => {
		return data.text()
	}).then((res) => {
		console.log(res);
		var parsed = JSON.parse(res);
		document.getElementById("login").style.display = "none";

		// var imgSrc = parsed["url"].startsWith("/") ? host + parsed["url"] : parsed["url"];

		let bodyRect = document.body.getBoundingClientRect();

		colorBGElem.style.width = (bodyRect.width + "px");
		colorBGElem.style.height = (bodyRect.height + "px");
		// colorBGElem.style.display = "none";

		imgElem = document.createElement("img");
		imgElem.id = "display_img";
		imgElem.style.width = (bodyRect.width + "px");
		imgElem.style.height = (bodyRect.height + "px");
		// imgElem.src = imgSrc;
		imgElem.style.display = "none";
		document.body.insertBefore(imgElem, document.body.childNodes[0]);

		colorBGElem.style.display = "";

		let rgb = parsed["rgb"];
		colorBGElem.style.backgroundColor = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;

		confirm()

		eventSource = new EventSource(`${hostApi}/serverloop/${loginVals["screenid"]}`);
		eventSource.onmessage = function(event) {
		  // document.getElementById("result").innerHTML += event.data + "<br>";
			let data = JSON.parse(event.data);
			if (data.hasOwnProperty("img_path")) {
				colorBGElem.style.display = "none";
				imgElem.style.display = "";

				let url = data["img_path"];
				imgSrc = url.startsWith("/") ? `${host}${url}` : url;
				document.getElementById("display_img").src = imgSrc;
			}
			else if (data.hasOwnProperty("img_url")) {
				colorBGElem.style.display = "none";
				imgElem.style.display = "";

				let url = data["img_url"];
				imgSrc = url.startsWith("/") ? `${host}${url}` : url;
				document.getElementById("display_img").src = imgSrc;	
			}
			else if (data.hasOwnProperty("rgb")) {
				imgElem.style.display = "none";
				colorBGElem.style.display = "";

				let rgb = data["rgb"];
				colorBGElem.style.backgroundColor = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
			}
			confirm()
		}; 
	});
}

function autofill() {
	let rect = document.body.getBoundingClientRect();
	document.getElementById("wPx").value = rect["width"] * window.devicePixelRatio;
	document.getElementById("hPx").value = rect["height"] * window.devicePixelRatio;


	document.getElementById("ppcm").value = ppcm * window.devicePixelRatio;

}

function confirm() {
	fetch(`${host}/api/confirm/${loginVals["screenid"]}`, {
		method: "GET"
	}).then(
		res => res.text()
	).then((res) => {
		console.log(res);
	});
}

