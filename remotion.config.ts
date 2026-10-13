import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setConcurrency(4);

// Remotion kendi Chrome'unu indiremezse (kapalı ağ), mevcut bir headless shell kullan:
// REMOTION_BROWSER=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
if (process.env.REMOTION_BROWSER) {
  Config.setBrowserExecutable(process.env.REMOTION_BROWSER);
}
