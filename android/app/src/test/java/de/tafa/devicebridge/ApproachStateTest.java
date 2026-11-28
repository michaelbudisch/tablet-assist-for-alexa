package de.tafa.devicebridge;
import org.junit.Test;
import static org.junit.Assert.*;
public class ApproachStateTest {
    @Test public void walkByCannotImmediatelyActivate(){
        ApproachState s=new ApproachState();
        assertFalse(s.update(0,40,25,4));
        assertFalse(s.update(400,0,25,4));
        assertFalse(s.update(900,40,25,4));
        assertTrue(s.update(1800,40,25,4));
    }
    @Test public void stationaryNearbyFaceStaysPresent(){
        ApproachState s=new ApproachState();s.update(0,30,25,4);
        for(int i=1;i<50;i++)assertTrue(s.update(i*1000L,30,25,4));
    }
    @Test public void exitDelayAndHysteresisPreventFlicker(){
        ApproachState s=new ApproachState();s.update(0,30,25,4);assertTrue(s.update(1000,30,25,4));
        assertTrue(s.update(2000,21,25,4));
        assertTrue(s.update(3000,0,25,4));assertTrue(s.update(6000,0,25,4));
        assertFalse(s.update(7000,0,25,4));
    }
    @Test public void renewedNearFaceCancelsExit(){
        ApproachState s=new ApproachState();s.update(0,30,25,4);s.update(1000,30,25,4);
        s.update(2000,0,25,4);assertTrue(s.update(3000,24,25,4));
        s.update(4000,0,25,4);assertTrue(s.update(7000,0,25,4));
    }
    @Test public void resetNeverKeepsOldPresence(){
        ApproachState s=new ApproachState();s.update(0,30,25,4);s.update(1000,30,25,4);s.clear();
        assertFalse(s.update(2000,30,25,4));
    }
    @Test public void longGapCannotConfirmOldCandidate(){
        ApproachState s=new ApproachState();s.update(0,30,25,4);
        assertFalse(s.update(10000,30,25,4));assertTrue(s.update(11000,30,25,4));
    }
    @Test public void onlyCentralFacesContributeAndOrientationUsesShortSide(){
        assertEquals(25,ApproachState.facePercent(640,480,260,160,380,300),.001);
        assertEquals(25,ApproachState.facePercent(480,640,180,230,300,370),.001);
        assertEquals(0,ApproachState.facePercent(640,480,0,100,100,250),0);
        assertEquals(0,ApproachState.facePercent(0,480,0,0,100,100),0);
    }
    @Test public void frontAndRearRotationAreCompensated(){
        assertEquals(0,new CameraRotation().imageDegrees(270,90,true));
        assertEquals(180,new CameraRotation().imageDegrees(270,90,false));
        assertEquals(270,new CameraRotation().imageDegrees(0,90,false));
    }
}
