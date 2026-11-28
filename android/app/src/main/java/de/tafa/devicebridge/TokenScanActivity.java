package de.tafa.devicebridge;

import android.os.Bundle;
import android.content.Context;
import android.view.WindowManager;
import com.journeyapps.barcodescanner.CaptureActivity;

/** The embedded scanner owns camera permissions and releases the camera on pause. */
public class TokenScanActivity extends CaptureActivity {
    @Override protected void attachBaseContext(Context base) { super.attachBaseContext(AppLanguage.wrap(base)); }
    @Override protected void onCreate(Bundle state) {
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        super.onCreate(state);
    }
}
