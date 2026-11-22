package de.jarvis.audio;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.drawable.BitmapDrawable;
import android.view.View;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.*;
import java.util.List;
import java.io.File;
import java.io.FileOutputStream;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.BooleanSupplier;

/** Runs only on our isolated emulator with emulated camera scenes, never a real camera or HA server. */
final class CameraSmoke {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    private static void await(Instrumentation test,BooleanSupplier condition,String message)throws Exception {
        long end=System.nanoTime()+15_000_000_000L;
        while(System.nanoTime()<end){
            AtomicBoolean passed=new AtomicBoolean();test.runOnMainSync(()->passed.set(condition.getAsBoolean()));
            if(passed.get())return;Thread.sleep(50);
        }
        throw new AssertionError(message);
    }
    static String run(Instrumentation test)throws Exception {
        Context context=test.getTargetContext();
        context.getSharedPreferences(MainActivity.PREF,0).edit().putString("ui_language","de").remove("camera_lens_id").commit();
        check(context.checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED,"Begin with camera permission denied");
        Intent launch=new Intent().setComponent(new ComponentName(context,CameraActivity.class)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        Activity camera=test.startActivitySync(launch);
        try {
            test.waitForIdleSync();
            Spinner spinner=camera.findViewById(R.id.camera_lens);
            check(spinner.getCount()>=2,"Emulator has front and rear camera");
            test.runOnMainSync(()->{
                check(((TextView)camera.findViewById(R.id.camera_status)).getText().toString().equals(camera.getString(R.string.camera_off)),"Opening never starts camera");
                check(!camera.findViewById(R.id.camera_capture).isEnabled(),"No capture before explicit start");
                check(spinner.getSelectedItem().toString().contains(camera.getString(R.string.camera_front)),"Default front camera");
                camera.findViewById(R.id.camera_start).performClick();
            });
            AccessibilityNodeInfo deny=null;
            for(int i=0;i<80&&deny==null;i++){
                AccessibilityNodeInfo root=test.getUiAutomation().getRootInActiveWindow();
                if(root!=null){List<AccessibilityNodeInfo> nodes=root.findAccessibilityNodeInfosByViewId("com.android.permissioncontroller:id/permission_deny_button");if(!nodes.isEmpty())deny=nodes.get(0);}
                if(deny==null)Thread.sleep(50);
            }
            check(deny!=null&&deny.performAction(AccessibilityNodeInfo.ACTION_CLICK),"Real permission prompt can be denied");
            await(test,()->((TextView)camera.findViewById(R.id.camera_status)).getText().toString().equals(camera.getString(R.string.camera_denied)),"Permission denial explained");
            check(!AudioService.running,"Permission denial never starts audio");
            test.getUiAutomation().grantRuntimePermission(context.getPackageName(),Manifest.permission.CAMERA);
            test.runOnMainSync(()->camera.findViewById(R.id.camera_start).performClick());
            await(test,()->camera.findViewById(R.id.camera_capture).isEnabled(),"Front camera preview becomes ready");
            test.runOnMainSync(()->camera.findViewById(R.id.camera_capture).performClick());
            await(test,()->camera.findViewById(R.id.camera_clear).isEnabled(),"Front JPEG capture completes");
            try(FileOutputStream file=new FileOutputStream(new File(context.getCacheDir(),"camera-tablet.png"))){
                Bitmap screen=test.getUiAutomation().takeScreenshot();
                check(screen!=null,"Camera screenshot available");screen.compress(Bitmap.CompressFormat.PNG,100,file);screen.recycle();
            }
            test.runOnMainSync(()->{
                ImageView image=camera.findViewById(R.id.camera_snapshot);
                check(image.getDrawable() instanceof BitmapDrawable,"Decoded JPEG shown");
                Bitmap bitmap=((BitmapDrawable)image.getDrawable()).getBitmap();
                check(bitmap.getWidth()>0&&bitmap.getHeight()>0&&(long)bitmap.getWidth()*bitmap.getHeight()<=1280L*960,"Snapshot resolution is bounded");
                check(((TextView)camera.findViewById(R.id.camera_snapshot_status)).getText().toString().contains("×"),"Snapshot has dimensions");
                camera.findViewById(R.id.camera_clear).performClick();
                check(image.getDrawable()==null&&!camera.findViewById(R.id.camera_clear).isEnabled(),"Clear removes image");
                camera.findViewById(R.id.camera_stop).performClick();
                check(!camera.findViewById(R.id.camera_capture).isEnabled()&&spinner.isEnabled(),"Stop resets capture and allows lens selection");
                spinner.setSelection(1);
            });
            test.waitForIdleSync();Thread.sleep(300);
            test.runOnMainSync(()->camera.findViewById(R.id.camera_start).performClick());
            await(test,()->camera.findViewById(R.id.camera_capture).isEnabled(),"Rear camera can open after front closes");
            test.runOnMainSync(()->camera.findViewById(R.id.camera_capture).performClick());
            await(test,()->camera.findViewById(R.id.camera_clear).isEnabled(),"Rear JPEG capture completes");
            Activity other=test.startActivitySync(new Intent().setComponent(new ComponentName(context,MainActivity.class)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            try{
                await(test,()->!camera.findViewById(R.id.camera_stop).isEnabled(),"Leaving screen stops camera");
                test.runOnMainSync(()->check(((ImageView)camera.findViewById(R.id.camera_snapshot)).getDrawable()==null,"Leaving screen clears snapshot"));
            }finally{test.runOnMainSync(other::finish);}
            test.waitForIdleSync();
            await(test,()->camera.findViewById(R.id.camera_start).isEnabled(),"Returning needs explicit start");
            check(!AudioService.running,"Camera test never changes audio service state");
            return "Camera smoke passed: opt-in, real permission denial, front/rear preview and JPEG, bounded image, clear/stop, background cleanup, no automatic restart.\n";
        }finally{test.runOnMainSync(camera::finish);}
    }
}
