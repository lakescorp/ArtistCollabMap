/**
 * Plays the audio associated with the given element ID.
 * @param {string} elementId - The ID of the audio element to play.
 */
function playAudio(elementId) {
    document.getElementById(elementId).play();
}

/**
 * Pauses the audio element with the specified ID.
 * @param {string} elementId - The ID of the audio element to pause.
 */
function pauseAudio(elementId) {
    document.getElementById(elementId).pause();
}

// Set up event listeners to play and pause audio when hovering over song thumbnails
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