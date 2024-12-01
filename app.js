// Spotify Client ID and Access Token (you need to replace these with real values)
const SPOTIFY_API_URL = "https://api.spotify.com";
const SPOTIFY_ACCESS_TOKEN = '8479a13f88bd43e88e31b3ae1527fc99';  // Replace with an actual access token

// Listen for input changes and trigger search
document.getElementById("searchInput").addEventListener("input", function() {
    const query = this.value.trim();

    if (query.length >= 3) {  // Start search after 3 characters
        searchSpotify(query);
    } else {
        document.getElementById("searchResults").innerHTML = '';  // Clear results if query is too short
    }
});

function searchSpotify(query) {
    // Spotify API search endpoint for tracks, albums, and artists
    fetch(`${SPOTIFY_API_URL}search?q=${encodeURIComponent(query)}&type=track,album,artist&limit=10`, {
        headers: {
            Authorization: `Bearer ${SPOTIFY_ACCESS_TOKEN}`
        }
    })
    .then(response => response.json())
    .then(data => {
        const results = data;  // Contains track, album, and artist results
        displaySearchResults(results);
    })
    .catch(error => {
        console.error('Error fetching data from Spotify API:', error);
    });
}

function displaySearchResults(results) {
    const searchResultsContainer = document.getElementById("searchResults");
    searchResultsContainer.innerHTML = ''; // Clear previous results

    // Iterate through tracks, albums, and artists
    const items = [
        ...results.tracks.items,
        ...results.albums.items,
        ...results.artists.items
    ];

    // Display results in a list
    items.forEach(item => {
        const resultElement = document.createElement("div");
        resultElement.classList.add("result-item");
        resultElement.innerHTML = `
            <img src="${item.images ? item.images[0]?.url : 'https://via.placeholder.com/50'}" alt="Image">
            <div>
                <h4>${item.name}</h4>
                <p>${item.type.charAt(0).toUpperCase() + item.type.slice(1)}</p>
            </div>
        `;

        // Add event listener to load the selected item into the Spotify player
        resultElement.addEventListener("click", () => playSpotifyItem(item.id, item.type));

        searchResultsContainer.appendChild(resultElement);
    });
}

function playSpotifyItem(id, type) {
    let iframeUrl = '';

    if (type === 'track') {
        iframeUrl = `https://open.spotify.com/embed/track/${id}`;
    } else if (type === 'album') {
        iframeUrl = `https://open.spotify.com/embed/album/${id}`;
    } else if (type === 'artist') {
        iframeUrl = `https://open.spotify.com/embed/artist/${id}`;
    }

    document.getElementById("spotifyPlayer").src = iframeUrl;  // Update the Spotify player
}
