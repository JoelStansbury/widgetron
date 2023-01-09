const { app, BrowserWindow } = require('electron')
const spawn = require("child_process").spawn;
const path = require('path')

const conda_activate_script = path.join(__dirname, '../../../../../../Scripts/activate');
const notebook_dir = path.join(__dirname,"../../../");
console.log(conda_activate_script);
const child = spawn("cmd.exe", [
  "/k",
  `"${conda_activate_script} && cd ${notebook_dir} && voila "{{filename}}" --no-browser --port=8866"`
  ], {
    shell:true,
    detached:true, // only way to kill voila
  }
);


const createWindow = () => {

    const win = new BrowserWindow({
      width: 1000,
      height: 600
    })
    win.loadFile('index.html')
    // win.webContents.openDevTools()
  }
app.whenReady().then(() => {
  createWindow()
})

// None of this works
// const kill = require('tree-kill');
// app.on("before-quit", () => {
  // spawn("taskkill", ["/PID", child.pid, '/F', "/T"]);
  // kill(child.pid, "SIGKILL");
  // child.kill("SIGKILL");
// })
