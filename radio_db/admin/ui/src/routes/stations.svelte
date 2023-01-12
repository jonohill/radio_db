<script>
    import { goto } from '$app/navigation';
    import { getStations } from '../client';

    const stationsPromise = getStations();
    let fields = [];
    stationsPromise.then(stations => {
        fields = Object.keys(stations[0]);
    });
</script>

{#await stationsPromise}
    <p>...</p>
{:then stations} 
    {#if stations.length > 0}
        <table class="table w-full">
            <thead>
                <tr>
                    {#each fields as field}
                        <th>{field}</th>
                    {/each}
                </tr>
            </thead>
            <tbody>
                {#each stations as station}
                <tr class="hover" on:click="{() => goto(`/stations/${station.id}`)}">              
                    {#each fields as field}
                        <td>{station[field]}</td>
                    {/each}
                </tr>
                {/each}
            </tbody>
        </table>
    {:else}
        <p>No stations yet</p>
    {/if}
{/await}

