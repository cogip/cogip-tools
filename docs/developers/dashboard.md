# Dashboard documentation

The dashboard is written with vanilla JS, CSS and HTML (and love). We made the choice to not used any frameworks like Angular or Vue.js... because dashboard is a very small web site.

This dashboard uses only two externals frameworks, which are Bootstrap and Socket.io.

Socket.io is useful to dynamically receive events from Copilot and display them.

Bootstrap is a framework very powerful which comes with layout conception (grid to help us with responsively) and components (like modal that we use). But Bootstrap is a very large and heavy framework and we only use a percentage of what it offers. So we made the choice to purge it to reduce loading time on dashboard.

!!! note "The manipulation below needs to be done each time we add or remove a class in html, css or js files in server."

This command line has to be executed in `cogip-tools/cogip/tools/dashboard`.

1. Install npm
   `sudo apt install npm`

2. Install PurgeCSS as CLI (you may need to be super user)
   `npm i -g purgecss`

3. Run command to purge Bootstrap file according to what we use in our html, js and css files
   `purgecss -css static/css/external/bootstrap-5.3.3.min.css --content templates/dashboard.html static/js/*.js --output static/css/purged`

Useful documentation:

- https://purgecss.com/CLI.html
