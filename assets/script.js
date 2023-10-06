function playAudio(elementId) {
    document.getElementById(elementId).play();
}

function pauseAudio(elementId) {
    document.getElementById(elementId).pause();
}

document.body.addEventListener('mouseover', function(event) {
    if(event.target && event.target.className === 'song-thumbnail') {
        let audioId = 'audio-' + event.target.dataset.songId;
        playAudio(audioId);
    }
});

document.body.addEventListener('mouseout', function(event) {
    if(event.target && event.target.className === 'song-thumbnail') {
        let audioId = 'audio-' + event.target.dataset.songId;
        pauseAudio(audioId);
    }
});