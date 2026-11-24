package de.jarvis.audio;

import org.junit.Test;
import static org.junit.Assert.*;

public class CameraRefreshTest {
    @Test public void boundedOptionsAndDefault() {
        assertArrayEquals(new int[]{1,2,3,5,10},CameraRefresh.options());
        for(int s:CameraRefresh.options())assertEquals(s,CameraRefresh.normalize(s));
        for(int s:new int[]{-1,0,4,15,60,Integer.MAX_VALUE})assertEquals(2,CameraRefresh.normalize(s));
    }
    @Test public void compensateForCaptureAndUpload() {
        assertEquals(1700L,CameraRefresh.nextDelay(2,300,true));
        assertEquals(9000L,CameraRefresh.nextDelay(10,1000,true));
        assertEquals(500L,CameraRefresh.nextDelay(1,800,true));
        assertEquals(500L,CameraRefresh.nextDelay(1,10000,true));
        assertEquals(2000L,CameraRefresh.nextDelay(2,-1,true));
    }
    @Test public void errorsBackOffAndOptionsAreIndependent() {
        assertEquals(5000L,CameraRefresh.nextDelay(1,100,false));
        int[] options=CameraRefresh.options();options[0]=0;
        assertEquals(1,CameraRefresh.options()[0]);
    }
}
