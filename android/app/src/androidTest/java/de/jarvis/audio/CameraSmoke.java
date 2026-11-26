package de.jarvis.audio;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.view.View;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.*;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.BooleanSupplier;

/** New unified Settings camera smoke. No local preview or test screen exists. */
final class CameraSmoke {
    private static void check(boolean ok,String error){if(!ok)throw new AssertionError(error);}
    private static void await(Instrumentation test,BooleanSupplier predicate,String error)throws Exception{
        long stop=System.nanoTime()+12_000_000_000L;
        while(System.nanoTime()<stop){
            AtomicBoolean yes=new AtomicBoolean();
            test.runOnMainSync(()->yes.set(predicate.getAsBoolean()));
            if(yes.get())return;
            Thread.sleep(50);
        }
        throw new AssertionError(error);
    }
    static String run(Instrumentation test)throws Exception{
        Context ctx=test.getTargetContext();
        var prefs=ctx.getSharedPreferences(MainActivity.PREF,0);
        prefs.edit().clear().putString("ui_language","de")
                .putString("base","http://192.168.1.10:8123")
                .putString(MainActivity.HTTP_CONSENT,"http://192.168.1.10:8123")
                .putString("secret",MainActivity.encrypt("camera-smoke-token")).commit();
        check(ctx.checkSelfPermission(Manifest.permission.CAMERA)
                !=PackageManager.PERMISSION_GRANTED, "Camera permission initially absent");
        Activity screen=test.startActivitySync(new Intent(ctx,MainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        try{
            test.waitForIdleSync();
            test.runOnMainSync(()->{
                screen.findViewById(R.id.nav_settings).performClick();
                check(screen.findViewById(R.id.section_settings).getVisibility()==View.VISIBLE,
                        "Unified Settings opens");
                Spinner lenses=screen.findViewById(R.id.camera_lens);
                check(lenses.getCount()>=2,"Camera lenses are discoverable");
                check(((Spinner)screen.findViewById(R.id.camera_refresh_rate)).getCount()==5,
                        "Refresh interval choices are present");
                CheckBox motion=screen.findViewById(R.id.camera_motion);
                motion.setChecked(true);
                check(prefs.getBoolean("camera_motion",false),"Motion option saves");
                motion.setChecked(false);
                check(!prefs.getBoolean("camera_motion",true),"Motion can be disabled");
                screen.findViewById(R.id.camera_relay_start).performClick();
            });
            AccessibilityNodeInfo deny=null;
            for(int i=0;i<80&&deny==null;i++){
                AccessibilityNodeInfo root=test.getUiAutomation().getRootInActiveWindow();
                if(root!=null){
                    List<AccessibilityNodeInfo> nodes=
                        root.findAccessibilityNodeInfosByViewId(
                            "com.android.permissioncontroller:id/permission_deny_button");
                    if(!nodes.isEmpty())deny=nodes.get(0);
                }
                if(deny==null)Thread.sleep(50);
            }
            check(deny!=null&&deny.performAction(AccessibilityNodeInfo.ACTION_CLICK),
                    "Camera permission prompt remains explicit and rejectable");
            await(test,()->((TextView)screen.findViewById(R.id.camera_relay_status))
                .getText().toString().equals(screen.getString(R.string.camera_denied)),
                "Denied permission is explained");
            check(!CameraRelayService.running,"Camera does not start on permission denial");
            test.runOnMainSync(()->{
                screen.findViewById(R.id.nav_status).performClick();
                check(screen.findViewById(R.id.section_status).getVisibility()==View.VISIBLE,
                        "Status is separate from camera controls");
                screen.findViewById(R.id.nav_settings).performClick();
                check(screen.findViewById(R.id.camera_relay_start).getVisibility()==View.VISIBLE,
                        "Camera controls remain in Settings");
            });
            return "Camera settings smoke passed: no preview/test activity, optics, motion, explicit permission, safe denial.\n";
        }finally{test.runOnMainSync(screen::finish);}
    }
}
