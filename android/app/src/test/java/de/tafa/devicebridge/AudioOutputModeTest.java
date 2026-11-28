package de.tafa.devicebridge;
import android.media.AudioDeviceInfo;
import org.junit.Test;
import static org.junit.Assert.*;
public class AudioOutputModeTest {
    @Test public void automaticPrefersBluetoothOtherwiseTablet(){
        assertEquals(AudioDeviceInfo.TYPE_BLUETOOTH_A2DP,AudioOutputMode.preferredType("auto",true));
        assertEquals(AudioDeviceInfo.TYPE_BUILTIN_SPEAKER,AudioOutputMode.preferredType("auto",false));
    }
    @Test public void strictModesDoNotSwitch(){
        assertEquals(AudioDeviceInfo.TYPE_BLUETOOTH_A2DP,AudioOutputMode.preferredType("bluetooth",false));
        assertEquals(AudioDeviceInfo.TYPE_BUILTIN_SPEAKER,AudioOutputMode.preferredType("tablet",true));
    }
    @Test public void invalidModesUseAutomatic(){assertEquals("auto",AudioOutputMode.normalize("invalid"));}
}
