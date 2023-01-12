<script>
    import { page } from "$app/stores";
    import { getLastPlayed, getStation } from "../../client";

    let station = {};
    let lastPlayed = [];

    Promise.all([
        getStation($page.params.id),
        getLastPlayed($page.params.id)
    ])
    .then(([s, lp]) => {
        station = s;
        lastPlayed = lp;
    });
</script>

<h1 class="text-xl">{station.name}</h1>

<ul>
    {#each lastPlayed as track}
        <li>{track.last_played}, {track.song.artist} - {track.song.title}</li>
    {/each}
</ul>
