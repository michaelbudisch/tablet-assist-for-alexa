package de.jarvis.audio;
import org.junit.Test;
import static org.junit.Assert.*;

public class CameraRotationTest {
    @Test public void physicalMountingOverridesLockedDisplayForBothLenses(){
        for(int sensor:new int[]{0,90,180,270})
            for(int pose:new int[]{0,90,180,270})
                for(boolean front:new boolean[]{false,true}){
                    CameraRotation rotation=new CameraRotation();rotation.update(pose);
                    for(int lockedDisplay:new int[]{0,90,180,270})
                        assertEquals(CameraRotation.normalize(sensor+(front?-pose:pose)),
                            rotation.imageDegrees(sensor,lockedDisplay,front));
                }
    }
    @Test public void usesDisplayUntilAUsablePhysicalPoseArrives(){
        CameraRotation r=new CameraRotation();r.update(-1);
        assertEquals(0,r.imageDegrees(270,90,true));
        assertEquals(180,r.imageDegrees(270,90,false));
        r.update(90);
        assertEquals(180,r.imageDegrees(270,90,true));
        assertEquals(0,r.imageDegrees(270,90,false));
    }
    @Test public void flatAndInvalidEventsKeepLastReliableMountingPose(){
        CameraRotation r=new CameraRotation();r.update(270);
        for(int unknown:new int[]{-1,-90,360,720}){
            r.update(unknown);assertEquals(0,r.imageDegrees(270,0,true));
        }
    }
    @Test public void hysteresisWorksAcrossAllQuadrantsAndWraparound(){
        for(int pose:new int[]{0,90,180,270}){
            CameraRotation r=new CameraRotation();r.update(pose);
            r.update((pose+59)%360);assertEquals(pose,r.imageDegrees(0,0,false));
            r.update((pose+60)%360);assertEquals((pose+90)%360,r.imageDegrees(0,0,false));
            r.update((pose+31)%360);assertEquals((pose+90)%360,r.imageDegrees(0,0,false));
            r.update((pose+30)%360);assertEquals(pose,r.imageDegrees(0,0,false));
        }
    }
    @Test public void halfTurnAndUnknownStartupAreSafe(){
        CameraRotation r=new CameraRotation();
        assertEquals(270,r.imageDegrees(0,90,false));
        r.update(180);assertEquals(270,r.imageDegrees(90,0,false));
        r.update(-1);assertEquals(270,r.imageDegrees(90,270,false));
    }
}
