import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, existsSync} from 'node:fs';
const read = p => readFileSync(new URL('../'+p, import.meta.url), 'utf8');

test('Android application has a unique ID and offline HTTPS WebViewAssetLoader', () => {
  const gradle = read('android/app/build.gradle');
  const java = read('android/app/src/main/java/vn/congtyxd3d/app/MainActivity.java');
  assert.match(gradle, /applicationId\s+'vn\.congtyxd3d\.app'/);
  assert.match(java, /WebViewAssetLoader/);
  assert.match(java, /https:\/\/appassets\.androidplatform\.net\/assets\/www\/index\.html/);
  assert.match(java, /setJavaScriptEnabled\(true\)/);
  assert.match(java, /setDomStorageEnabled\(true\)/);
});

test('Android allows file picker and keeps browser storage enabled', () => {
  const java = read('android/app/src/main/java/vn/congtyxd3d/app/MainActivity.java');
  assert.match(java, /onShowFileChooser/);
  assert.match(java, /setDatabaseEnabled\(true\)/);
  assert.match(java, /setAllowFileAccess\(false\)/);
});

test('Android manifest and GitHub APK build workflow exist', () => {
  const manifest = read('android/app/src/main/AndroidManifest.xml');
  const workflow = read('.github/workflows/build-android-apk.yml');
  assert.match(manifest, /android:exported="true"/);
  assert.match(manifest, /android:allowBackup="false"/);
  assert.match(workflow, /:app:assembleDebug/);
  assert.match(workflow, /actions\/upload-artifact@v4/);
});

test('APK packaging includes every top-level web asset root', () => {
  const workflow = read('.github/workflows/build-android-apk.yml');
  for (const dir of ['src','data','assets']) {
    assert.ok(existsSync(new URL('../'+dir, import.meta.url)));
    assert.match(workflow, /cp -r src data assets/);
  }
  assert.match(workflow, /cp index\.html/);
});
