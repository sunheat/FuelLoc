// Preferences and places live in FuelLoc's local data store, not browser storage.
let workspacePreferences = {};
let savedLocations = [];
let preferenceWrites = Promise.resolve();
let locationToName = null;

async function stateRequest(url, method = 'GET', data) {
    const response = await fetch(url, {
        method,
        headers: {'Content-Type': 'application/json'},
        body: data === undefined ? undefined : JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Local data could not be saved or loaded. Please retry.');
    return response.json();
}

function savePreferences(values) {
    Object.assign(workspacePreferences, values);
    preferenceWrites = preferenceWrites.then(() => stateRequest('/api/preferences', 'PUT', values))
        .catch(error => displayToast(error.message));
}

async function loadWorkspaceState() {
    try {
        const state = await stateRequest('/api/user_state');
        workspacePreferences = state.preferences;
        savedLocations = state.locations;
        document.getElementById('darkModeSwitch').checked = workspacePreferences.dark_mode;
        document.body.classList.toggle('dark-mode', workspacePreferences.dark_mode);
        document.getElementById('enableFuelPrices').checked = workspacePreferences.fuel_enabled;
        document.getElementById('fuelRegion').value = workspacePreferences.fuel_region;
    } catch (error) {
        displayToast(error.message);
    }
    renderSavedLocations();
}

async function openSavedLocations() {
    try {
        savedLocations = (await stateRequest('/api/user_state')).locations;
        renderSavedLocations();
    } catch (error) {
        displayToast(error.message);
    }
    document.getElementById('savedPlacesDialog').showModal();
}

function renderSavedLocations() {
    const list = document.getElementById('savedPlacesList');
    list.replaceChildren();
    document.getElementById('noSavedPlaces').hidden = savedLocations.length > 0;
    for (const place of savedLocations) {
        const row = document.createElement('li');
        const preview = document.createElement('button');
        preview.type = 'button';
        preview.className = 'place-preview btn btn-outline-secondary';
        preview.textContent = place.name || `${place.lat}, ${place.lng}`;
        preview.title = `${place.lat}, ${place.lng}`;
        preview.addEventListener('click', () => {
            const position = [place.lat, place.lng];
            if (marker) marker.setLatLng(position);
            else marker = createMarker(position);
            setCoordinates(...position);
            map.setView(position, 13);
            document.getElementById('savedPlacesDialog').close();
        });
        const rename = document.createElement('button');
        rename.type = 'button';
        rename.className = 'btn btn-outline-secondary';
        rename.textContent = '✎';
        rename.setAttribute('aria-label', `Name ${place.name || 'this location'}`);
        rename.title = 'Name this location';
        rename.addEventListener('click', () => nameLocation(place));
        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'btn btn-outline-danger';
        remove.textContent = '×';
        remove.setAttribute('aria-label', `Delete ${place.name || 'this location'}`);
        remove.title = 'Delete location';
        remove.addEventListener('click', async () => {
            if (place.name && !confirm(`Delete "${place.name}"?`)) return;
            try {
                savedLocations = await stateRequest(`/api/locations/${place.id}`, 'DELETE');
                renderSavedLocations();
                document.getElementById('savePlace').focus();
            } catch (error) {
                displayToast(error.message);
            }
        });
        row.append(preview, rename, remove);
        list.append(row);
    }
}

function nameLocation(place) {
    locationToName = place;
    document.getElementById('placeName').value = place.name || '';
    document.getElementById('placeNameCoordinates').textContent = `${place.lat}, ${place.lng}`;
    document.getElementById('locationNameDialog').showModal();
    document.getElementById('placeName').focus();
}

function saveCurrentPlace() {
    if (!marker) return;
    const {lat, lng} = marker.getLatLng();
    nameLocation(savedLocations.find(place => place.lat === lat && place.lng === lng) || {lat, lng});
}

async function submitLocationName(event) {
    event.preventDefault();
    const button = document.getElementById('savePlaceName');
    button.disabled = true;
    try {
        savedLocations = await stateRequest('/api/locations', 'POST', {
            ...locationToName, name: document.getElementById('placeName').value.trim(),
        });
        renderSavedLocations();
        document.getElementById('locationNameDialog').close();
    } catch (error) {
        displayToast(error.message);
    } finally {
        button.disabled = false;
    }
}
