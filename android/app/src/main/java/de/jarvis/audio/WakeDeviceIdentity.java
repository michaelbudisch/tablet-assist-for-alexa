package de.jarvis.audio;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.UUID;

/** Random per-installation ID. It is routing metadata, not an authentication token. */
final class WakeDeviceIdentity {
    private WakeDeviceIdentity(){}
    static synchronized String get(Context ctx){
        SharedPreferences prefs=ctx.getSharedPreferences(MainActivity.PREF,0);
        String saved=prefs.getString("wake_device_id","");
        if(saved.matches("[0-9a-f]{32}"))return saved;
        String id=UUID.randomUUID().toString().replace("-","");
        prefs.edit().putString("wake_device_id",id).apply();
        return id;
    }
    static int slot(Context ctx){
        return Math.max(1,Math.min(4,ctx.getSharedPreferences(MainActivity.PREF,0)
            .getInt("wake_slot",1)));
    }
    static String room(Context ctx){
        String text=ctx.getSharedPreferences(MainActivity.PREF,0).getString("wake_room_name","").trim();
        return text.length()>35?text.substring(0,35):text.isEmpty()?"Tablet "+slot(ctx):text;
    }
}
