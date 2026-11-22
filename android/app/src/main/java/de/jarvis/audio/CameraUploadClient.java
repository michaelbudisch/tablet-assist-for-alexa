package de.jarvis.audio;

import org.json.JSONObject;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;

/** Same-origin authenticated push; no image listener/port on the tablet and no redirect forwarding. */
final class CameraUploadClient implements AutoCloseable {
    static final String API="/api/jarvis_echo_relay";
    private final String base,token,consent,device;
    private volatile HttpURLConnection current;
    private volatile boolean closed;
    private volatile String session="";
    private long sequence;
    CameraUploadClient(String base,String token,String consent,String device)throws Exception{
        this.base=HaAddress.validateStored(base,consent);this.token=token;this.consent=consent;this.device=device;
    }
    private HttpURLConnection connect(String path,String method)throws Exception{
        if(closed)throw new InterruptedIOException("cancelled");
        HttpURLConnection connection=(HttpURLConnection)new URL(HaAddress.validateStored(base,consent)+API+path).openConnection();
        current=connection;connection.setConnectTimeout(5000);connection.setReadTimeout(8000);
        connection.setInstanceFollowRedirects(false);connection.setRequestMethod(method);
        connection.setRequestProperty("Authorization","Bearer "+token);
        connection.setRequestProperty("X-Relay-Device",device);
        if(!session.isEmpty())connection.setRequestProperty("X-Relay-Session",session);
        if(closed){connection.disconnect();throw new InterruptedIOException("cancelled");}
        return connection;
    }
    private void check(int code)throws IOException {
        if(code==401||code==403)throw new IOException("camera_auth_error");
        if(code==404)throw new IOException("camera_integration_missing");
        if(code==409)throw new IOException("camera_pairing_error");
        if(code<200||code>=300)throw new IOException("camera_upload_error");
    }
    void upload(CameraJpeg.Frame frame,long capturedAt,Boolean motion)throws Exception{
        if(session.isEmpty()){
            HttpURLConnection connection=connect("/register","POST");
            try{
                byte[] data=new JSONObject().put("device_id",device).toString().getBytes(StandardCharsets.UTF_8);
                connection.setDoOutput(true);connection.setRequestProperty("Content-Type","application/json");connection.setFixedLengthStreamingMode(data.length);
                try(OutputStream output=connection.getOutputStream()){output.write(data);}
                check(connection.getResponseCode());
                ByteArrayOutputStream result=new ByteArrayOutputStream();
                try(InputStream input=connection.getInputStream()){
                    byte[] block=new byte[1024];int n;
                    while((n=input.read(block))!=-1){if(result.size()+n>4096)throw new IOException("camera_upload_error");result.write(block,0,n);}
                }
                String issued=new JSONObject(new String(result.toByteArray(),StandardCharsets.UTF_8)).getString("session");
                if(!issued.matches("[a-f0-9]{64}"))throw new IOException("camera_upload_error");
                if(closed)throw new InterruptedIOException("cancelled");session=issued;sequence=0;
            }finally{connection.disconnect();current=null;}
        }
        HttpURLConnection connection=connect("/frame","POST");
        try{
            connection.setDoOutput(true);connection.setRequestProperty("Content-Type","image/jpeg");
            connection.setRequestProperty("X-Relay-Sequence",Long.toString(++sequence));
            connection.setRequestProperty("X-Relay-Captured-At",Long.toString(capturedAt));
            connection.setRequestProperty("X-Relay-Motion",motion==null?"off":motion?"1":"0");
            connection.setFixedLengthStreamingMode(frame.jpeg.length);
            try(OutputStream output=connection.getOutputStream()){output.write(frame.jpeg);}
            int status=connection.getResponseCode();
            if(status==409){session="";throw new IOException("camera_upload_error");}
            check(status);
        }finally{connection.disconnect();current=null;}
    }
    @Override public void close(){
        closed=true;
        HttpURLConnection active=current;
        String oldSession=session;
        Thread cleanup=new Thread(()->{
            if(active!=null)active.disconnect();
            if(oldSession.isEmpty())return;
            HttpURLConnection ending=null;
            try{
                ending=(HttpURLConnection)new URL(base+API+"/frame").openConnection();
                ending.setConnectTimeout(3000);ending.setReadTimeout(3000);ending.setInstanceFollowRedirects(false);ending.setRequestMethod("DELETE");
                ending.setRequestProperty("Authorization","Bearer "+token);ending.setRequestProperty("X-Relay-Device",device);
                ending.setRequestProperty("X-Relay-Session",oldSession);ending.getResponseCode();
            }catch(Exception ignored){}finally{if(ending!=null)ending.disconnect();}
        },"relay-camera-stop");cleanup.setDaemon(true);cleanup.start();
    }
}
