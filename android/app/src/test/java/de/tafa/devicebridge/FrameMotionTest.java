package de.tafa.devicebridge;
import org.junit.Test;
import java.util.Arrays;
import static org.junit.Assert.*;

public class FrameMotionTest {
    @Test public void firstFrameAndStaticSceneHaveNoMovement(){
        FrameMotion detector=new FrameMotion();int[] image=new int[3072];Arrays.fill(image,60);
        assertFalse(detector.changed(image));assertFalse(detector.changed(image));
    }
    @Test public void globalLightingChangesAreIgnored(){
        FrameMotion detector=new FrameMotion();int[] image=new int[3072];Arrays.fill(image,40);detector.changed(image);
        Arrays.fill(image,180);assertFalse(detector.changed(image));
    }
    @Test public void localMovementAndReset(){
        FrameMotion detector=new FrameMotion();int[] image=new int[3072];detector.changed(image);
        Arrays.fill(image,0,500,180);assertTrue(detector.changed(image));
        detector.clear();assertFalse(detector.changed(image));
    }
}
