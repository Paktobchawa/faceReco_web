const video = document.getElementById("camera");

navigator.mediaDevices.getUserMedia({video: true, audio: false})
    .then(function (stream) {
        video.srcObject = stream;
    })
    .catch(function (error) {
        console.error(error);
    })