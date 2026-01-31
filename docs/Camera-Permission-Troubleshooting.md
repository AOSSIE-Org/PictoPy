# Camera Permission Troubleshooting

This guide explains why camera access may become permanently blocked in PictoPy on Windows, and how to recover from it.

## Why Camera Permission Gets Stuck

When you click **"Don't Allow"** on the camera permission prompt in PictoPy, the denial is **not** stored in Settings. Instead, it's stored by the app's internal web engine (WebView2) at the Chromium layer.

---

## Recovery Steps

### Windows:

!!! warning "This is a destructive workaround"

> Deleting the WebView2 data folder will reset:
>
> -   Camera permission (allowing re-prompt)
> -   Onboarding state
> -   Avatar/name selection
> -   Any other local webview data
>
> Use this as a **last resort** only.

#### Step 1: Close PictoPy

Make sure PictoPy is completely closed before proceeding.

#### Step 2: Locate the WebView2 Data Folder

Open **File Explorer** and navigate to:

```
%LOCALAPPDATA%\org.aossie.pictopy
```

You can paste this path directly into the File Explorer address bar.

#### Step 3: Delete the `EBWebView` Folder

Right-click the `EBWebView` folder and select **Delete**.

#### Step 4: Restart PictoPy

Launch PictoPy again. When you try to use the webcam feature, you'll be prompted for camera permission again.

---

## Still Need Help?

If you're still experiencing issues after following these steps, please [open an issue on GitHub](https://github.com/aossie-org/PictoPy/issues/new?template=bug.yml) with:

-   Your Platform (Windows, Linux, macOS)
-   Steps you've already tried
-   Any error messages you see
