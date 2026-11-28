package de.tafa.devicebridge;
import android.content.Context;
import android.content.SharedPreferences;
import android.media.AudioDeviceInfo;
import android.media.AudioManager;
final class AudioOutputMode {
    static final String KEY="audio_output_mode", PENDING="audio_output_pending";
    static final String AUTO="auto", BLUETOOTH="bluetooth", TABLET="tablet";
    static final String[] MODES={AUTO,BLUETOOTH,TABLET};
    private AudioOutputMode(){}
    static boolean valid(String v){return AUTO.equals(v)||BLUETOOTH.equals(v)||TABLET.equals(v);}
    static String normalize(String v){return valid(v)?v:AUTO;}
    static SharedPreferences prefs(Context c){return c.getSharedPreferences(MainActivity.PREF,0);}
    static String get(Context c){return normalize(prefs(c).getString(KEY,AUTO));}
    static void choose(Context c,String v){if(valid(v))prefs(c).edit().putString(KEY,v).putString(PENDING,v).apply();}
    static void applyRemote(Context c,String v){SharedPreferences p=prefs(c);if(valid(v)&&!p.contains(PENDING)&&!v.equals(get(c)))p.edit().putString(KEY,v).apply();}
    static int preferredType(String v,boolean bt){return !TABLET.equals(v)&&(BLUETOOTH.equals(v)||bt)?AudioDeviceInfo.TYPE_BLUETOOTH_A2DP:AudioDeviceInfo.TYPE_BUILTIN_SPEAKER;}
    static AudioDeviceInfo find(AudioManager a,int type){if(a!=null)for(AudioDeviceInfo d:a.getDevices(AudioManager.GET_DEVICES_OUTPUTS))if(d.getType()==type)return d;return null;}
    static int select(AudioManager a,String v){return preferredType(v,find(a,AudioDeviceInfo.TYPE_BLUETOOTH_A2DP)!=null);}
    static String label(int type){return type==AudioDeviceInfo.TYPE_BLUETOOTH_A2DP?BLUETOOTH:TABLET;}
}
