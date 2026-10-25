import { Config } from '@remotion/cli/config';

// Kare görüntü biçimi ve kodek (YouTube uyumlu H.264 MP4).
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setCodec('h264');
Config.setPixelFormat('yuv420p');
// WebGL (Three.js) için. GPU'lu bir bilgisayarda 'angle' hızlıdır;
// GPU'suz sunucuda REMOTION_GL=swangle ile yazılım çizici kullanılır.
Config.setChromiumOpenGlRenderer((process.env.REMOTION_GL as 'angle' | 'swangle' | undefined) ?? 'angle');
