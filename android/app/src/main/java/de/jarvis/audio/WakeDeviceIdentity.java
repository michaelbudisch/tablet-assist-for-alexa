package de.jarvis.audio;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.UUID;

/** Random and persistent installation ID; no fixed tablet count. */
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
    static String room(Context ctx){
        String text=ctx.getSharedPreferences(MainActivity.PREF,0).getString("wake_room_name","").trim();
        return text.length()>48?text.substring(0,48):text.isEmpty()?"Jarvis Tablet":text;
    }
}
