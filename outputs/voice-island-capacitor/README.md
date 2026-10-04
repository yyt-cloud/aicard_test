# 灵感岛屿 Android 封装工程

现有 HTML 的 Capacitor WebView 首版工程，桌面图标采用 Clear Glass 方案 02。

## 构建 Debug APK

需要 Node.js、JDK 21、Android Studio/SDK。

```sh
npm install
npm run android:add
npx capacitor-assets generate --android
npm run android:apk
```

APK 路径：`android/app/build/outputs/apk/debug/app-debug.apk`。

真机中的 `127.0.0.1` 指向手机自身。测试语音前，应把 HTML 的 API 地址改为电脑局域网 IP；发布时必须改为公网 HTTPS。Android 端还需配置麦克风权限，并验证 WebView 的录音格式。
