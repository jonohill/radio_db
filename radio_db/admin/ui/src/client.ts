
export async function getStations() {
    const response = await fetch('/api/stations/');
    const data = await response.json();
    return data;
}


export async function getStation(id: string) {
    const response = await fetch('/api/stations/' + id);
    const data = await response.json();
    return data;
}


export async function getLastPlayed(stationId: string) {
    const response = await fetch(`/api/stations/${stationId}/last-played`);
    const data = await response.json();
    return data;
}
