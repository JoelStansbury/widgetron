# widgetron
App bundler for ipywidgets
## TODO
- Make a shortcut for the exe (maybe via post_install script)
- Test on mac and linux
- Make `.ico` file to finalize the example
- Quit `voila` programatically
  - `voila` is launched on [main.js#L8](https://github.com/JoelStansbury/widgetron/blob/main/src/widgetron/templates/electron/main.js#L8). It seems to disconnect `voila` from the spawned process somehow, so it's proving difficult to kill.
