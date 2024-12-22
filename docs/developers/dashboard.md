# Dashboard documentation

The dashboard is written with vanilla JS, CSS and HTML (and love). We made the choice to not used any frameworks like Angular or Vue.js... because dashboard is a very small web site.

This dashboard uses only two externals frameworks, which are TailwindCSS and Socket.io.

Socket.io is useful to dynamically receive events from Copilot and display them.

TailwindCSS is a utility-first CSS framework packed with classes like flex, pt-4, text-center and rotate-90 that can be composed to build any design.

!!! note "The manipulation below needs to be done each time we add or remove a class in html, css or js files in server."

This command line has to be executed in `cogip-tools/cogip/tools/dashboard` or `cogip-tools/cogip/tools/dashboard_beacon`.

1. Install npm
   `sudo apt install npm`

2. Install PurgeCSS as CLI (you may need to be super user)
   `npm install`

3. Run command to generate css file according to what we use in our html, js and css files
   `npx tailwindcss -i cogip/tools/dashboard/static/css/input.css -o cogip/tools/dashboard/static/css/prod/output.css --watch --minify`

Useful documentation:

[- https://purgecss.com/CLI.html](https://tailwindcss.com/docs/)
