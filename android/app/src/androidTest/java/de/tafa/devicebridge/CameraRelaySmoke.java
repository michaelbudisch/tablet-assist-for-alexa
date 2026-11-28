package de.tafa.devicebridge;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.graphics.BitmapFactory;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

/** Real background camera -> normalized JPEG -> authenticated local HTTP on an isolated emulator. */
final class CameraRelaySmoke {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    static String run(Instrumentation test)throws Exception{
        Context context=test.getTargetContext();
        test.getUiAutomation().grantRuntimePermission(context.getPackageName(),Manifest.permission.CAMERA);
        test.getUiAutomation().grantRuntimePermission(context.getPackageName(),Manifest.permission.POST_NOTIFICATIONS);
        String address=null;
        Enumeration<NetworkInterface> networks=NetworkInterface.getNetworkInterfaces();
        while(networks.hasMoreElements()){
            NetworkInterface network=networks.nextElement();
            Enumeration<InetAddress> addresses=network.getInetAddresses();
            while(addresses.hasMoreElements()){
                InetAddress candidate=addresses.nextElement();
                if(candidate instanceof Inet4Address&&candidate.isSiteLocalAddress())address=candidate.getHostAddress();
            }
        }
        check(address!=null,"Emulator has private network address");
        try(Receiver receiver=new Receiver()){
            String base="http://"+address+":"+receiver.socket.getLocalPort();
            var prefs=context.getSharedPreferences(MainActivity.PREF,0);
            prefs.edit().putString("base",base).putString(MainActivity.HTTP_CONSENT,base)
                    .putString("secret",MainActivity.encrypt("camera-fixture-only"))
                    .putBoolean("camera_motion",true).commit();
            Activity visible=test.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            try{
                check(!CameraRelayService.running,"Opening screen never auto-starts relay");
                test.runOnMainSync(()->{
                    visible.findViewById(R.id.nav_settings).performClick();
                    visible.findViewById(R.id.camera_relay_start).performClick();
                });
                check(receiver.first.await(15,TimeUnit.SECONDS),"First real camera JPEG uploaded: "+CameraRelayService.status);
                test.runOnMainSync(visible::finish);
                check(receiver.background.await(12,TimeUnit.SECONDS),"Camera keeps uploading after activity exits");
                check(CameraRelayService.running&&CameraRelayService.sent>=2,"Independent foreground camera remains running");
                context.stopService(new Intent(context,CameraRelayService.class));
                check(receiver.stopped.await(6,TimeUnit.SECONDS),"Stop invalidates remote camera session");
                long deadline=System.nanoTime()+3_000_000_000L;
                while(CameraRelayService.running&&System.nanoTime()<deadline)Thread.sleep(20);
                check(!CameraRelayService.running,"Camera service stopped");
                check(receiver.error==null,"HTTP protocol valid: "+receiver.error);
                check(!AudioService.running,"Camera does not start audio service");
            }finally{
                context.stopService(new Intent(context,CameraRelayService.class));test.runOnMainSync(visible::finish);
            }
        }
        return "Camera relay passed: real background camera, bounded upright JPEG, authenticated push/session/sequence, motion metadata, continued delivery after screen exit, remote stop.\n";
    }
    private static final class Receiver implements AutoCloseable {
        final ServerSocket socket=new ServerSocket(0);
        final CountDownLatch first=new CountDownLatch(1),background=new CountDownLatch(1),stopped=new CountDownLatch(1);
        volatile Throwable error;
        volatile boolean closed;
        int frames;
        String device;
        final String session=String.join("",Collections.nCopies(64,"a"));
        final Thread worker;
        Receiver()throws IOException{
            worker=new Thread(()->{
                while(!closed)try(Socket peer=socket.accept()){
                    peer.setSoTimeout(5000);InputStream input=peer.getInputStream();
                    String request=line(input);Map<String,String> headers=new HashMap<>();String header;
                    while(!(header=line(input)).isEmpty()){
                        int colon=header.indexOf(':');headers.put(header.substring(0,colon).toLowerCase(Locale.ROOT),header.substring(colon+1).trim());
                    }
                    int length=Integer.parseInt(headers.getOrDefault("content-length","0"));
                    check(length<=2*1024*1024,"Bounded HTTP body");
                    byte[] body=new byte[length];int offset=0,n;
                    while(offset<length&&(n=input.read(body,offset,length-offset))>0)offset+=n;
                    check(offset==length,"Complete body");
                    check(headers.get("authorization").equals("Bearer camera-fixture-only"),"HA bearer authentication");
                    byte[] reply=new byte[0];int status=204;
                    if(request.startsWith("POST /api/tablet_assist_for_alexa/room_camera/register ")){
                        device=headers.get("x-relay-device");
                        check(device!=null&&device.matches("[a-f0-9]{32}"),"Stable device ID");
                        check(new String(body,StandardCharsets.UTF_8).contains(device),"Pairing body matches device");
                        reply=("{\"session\":\""+session+"\"}").getBytes(StandardCharsets.UTF_8);status=200;
                    }else{
                        check(session.equals(headers.get("x-relay-session"))&&device.equals(headers.get("x-relay-device")),"Session and device headers");
                        if(request.startsWith("DELETE /api/tablet_assist_for_alexa/room_camera/frame "))stopped.countDown();
                        else{
                            check(request.startsWith("POST /api/tablet_assist_for_alexa/room_camera/frame "),"Fixed same-origin image path");
                            check("image/jpeg".equals(headers.get("content-type")),"JPEG content type");
                            BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;
                            BitmapFactory.decodeByteArray(body,0,body.length,bounds);
                            check(bounds.outWidth>0&&bounds.outHeight>0&&(long)bounds.outWidth*bounds.outHeight<=1280L*960,"Valid bounded JPEG");
                            check(Integer.parseInt(headers.get("x-relay-sequence"))==++frames,"Monotonic image sequence");
                            check(Long.parseLong(headers.get("x-relay-captured-at"))>0,"Capture timestamp");
                            check(Arrays.asList("0","1").contains(headers.get("x-relay-motion")),"Motion flag");
                            first.countDown();if(frames>=3)background.countDown();
                        }
                    }
                    OutputStream output=peer.getOutputStream();output.write(("HTTP/1.1 "+status+" OK\r\nContent-Type: application/json\r\nContent-Length: "+reply.length+"\r\nConnection: close\r\n\r\n").getBytes(StandardCharsets.US_ASCII));output.write(reply);output.flush();
                }catch(Throwable failure){if(!closed){error=failure;first.countDown();background.countDown();stopped.countDown();}}
            },"camera-fixture-receiver");worker.start();
        }
        private static String line(InputStream input)throws IOException{
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();int c;
            while((c=input.read())!=-1){if(c=='\n')break;if(c!='\r')bytes.write(c);if(bytes.size()>4096)throw new IOException("Header too long");}
            if(c==-1&&bytes.size()==0)throw new EOFException();return new String(bytes.toByteArray(),StandardCharsets.US_ASCII);
        }
        public void close()throws Exception{closed=true;socket.close();worker.join(2000);}
    }
}
