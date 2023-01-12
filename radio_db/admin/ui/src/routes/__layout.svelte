<script>
    import "../app.css";
</script>

<div>
    <div class="navbar bg-base-100">
        <div class="flex-none">
            <button class="btn btn-square btn-ghost">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    class="inline-block w-5 h-5 stroke-current"
                    ><path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M4 6h16M4 12h16M4 18h16"
                    /></svg
                >
            </button>
        </div>
        <a class="btn btn-ghost normal-case text-xl" href="/">radio db</a>
    </div>
    
    <div class="h-screen drawer drawer-mobile w-full">
        <input id="sidebar-toggle" type="checkbox" class="drawer-toggle" />
        <div class="flex flex-col items-center justify-center drawer-content">
            <!-- Page content here -->
            <!-- <label for="my-drawer-2" class="btn btn-primary drawer-button lg:hidden">Open drawer</label> -->
            <slot />
        </div>
        <div class="drawer-side">
            <label for="my-drawer-2" class="drawer-overlay" />
            <ul class="menu p-4 overflow-y-auto w-80 bg-base-100 text-base-content">
                <li><a href="/stations">Stations</a></li>
            </ul>
        </div>
    </div>
</div>

