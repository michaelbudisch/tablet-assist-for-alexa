package de.jarvis.audio;
import android.media.Image;
import java.nio.ByteBuffer;

/** One reusable, bounded NV21 snapshot; the camera image can be closed immediately. */
final class ApproachYuv {
    static byte[] copy(Image image,byte[] reuse){
        int w=image.getWidth(),h=image.getHeight();
        if(w<2||h<2||(w&1)!=0||(h&1)!=0||(long)w*h>1280L*960)
            throw new IllegalArgumentException("Unsupported analysis dimensions");
        int size=w*h;
        byte[] out=reuse!=null&&reuse.length==size+size/2?reuse:new byte[size+size/2];
        Image.Plane[] p=image.getPlanes();
        if(p.length!=3)throw new IllegalArgumentException("YUV planes required");
        ByteBuffer y=p[0].getBuffer().duplicate(),u=p[1].getBuffer().duplicate(),v=p[2].getBuffer().duplicate();
        int by=y.position(),bu=u.position(),bv=v.position();
        for(int row=0;row<h;row++){
            int offset=by+row*p[0].getRowStride();
            if(p[0].getPixelStride()==1){y.position(offset);y.get(out,row*w,w);}
            else for(int col=0;col<w;col++)out[row*w+col]=y.get(offset+col*p[0].getPixelStride());
        }
        for(int row=0;row<h/2;row++)for(int col=0;col<w/2;col++){
            int offset=size+row*w+col*2;
            out[offset]=v.get(bv+row*p[2].getRowStride()+col*p[2].getPixelStride());
            out[offset+1]=u.get(bu+row*p[1].getRowStride()+col*p[1].getPixelStride());
        }
        return out;
    }
}
