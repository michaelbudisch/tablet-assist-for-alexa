package de.tafa.devicebridge;

import android.content.Context;
import java.io.*;
import java.net.URL;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import javax.net.ssl.HttpsURLConnection;

/** Private, offline German Vosk model, installed after the user selects wakeword recognition. */
final class WakeModelInstaller {
    static final String MODEL_NAME="vosk-model-small-de-0.15";
    static final String DOWNLOAD="https://alphacephei.com/vosk/models/"+MODEL_NAME+".zip";
    private static final long ZIP_LIMIT=85L*1024*1024;
    private static final long UNPACK_LIMIT=300L*1024*1024;

    interface Progress { void onProgress(String status); }
    static File modelDir(Context context) { return new File(context.getFilesDir(),MODEL_NAME); }
    static boolean installed(Context context) {
        File dir=modelDir(context);
        return new File(dir,"conf/model.conf").isFile()&&new File(dir,"am/final.mdl").isFile();
    }
    private static void notify(Progress p,String s) { if(p!=null)p.onProgress(s); }

    static synchronized void install(Context context,Progress callback) throws Exception {
        if(installed(context)){notify(callback,"ready");return;}
        File root=context.getFilesDir(),archive=new File(root,"wake-model-downloading.zip");
        File unpack=new File(root,"wake-model-unpack");
        deleteTree(unpack);
        if(!unpack.mkdirs())throw new IOException("Unable to create model staging directory");
        try {
            URL url=new URL(DOWNLOAD);
            if(!url.getProtocol().equals("https")||!url.getHost().equals("alphacephei.com"))throw new IOException("Untrusted model origin");
            HttpsURLConnection connection=(HttpsURLConnection)url.openConnection();
            connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(15000);
            connection.setReadTimeout(20000);
            connection.setRequestProperty("Accept","application/zip");
            try {
                if(connection.getResponseCode()!=200)throw new IOException("Download HTTP "+connection.getResponseCode());
                long expected=connection.getContentLengthLong();
                if(expected>ZIP_LIMIT)throw new IOException("Model archive exceeds limit");
                try(InputStream in=new BufferedInputStream(connection.getInputStream());
                    OutputStream out=new BufferedOutputStream(new FileOutputStream(archive))){
                    byte[] b=new byte[32768];
                    int n;long size=0,lastMB=-1;
                    notify(callback,"downloading");
                    while((n=in.read(b))!=-1){
                        size+=n;
                        if(size>ZIP_LIMIT)throw new IOException("Archive too large");
                        out.write(b,0,n);
                        long mb=size/(1024*1024);
                        if(mb!=lastMB){lastMB=mb;notify(callback,"download "+mb+" MB");}
                    }
                }
            }finally{connection.disconnect();}
            notify(callback,"unpacking");
            long total=0;
            try(ZipInputStream zin=new ZipInputStream(new BufferedInputStream(new FileInputStream(archive)))){
                ZipEntry entry;
                while((entry=zin.getNextEntry())!=null){
                    String name=entry.getName().replace('\\','/');
                    if(!name.startsWith(MODEL_NAME+"/"))throw new IOException("Unexpected model directory");
                    String relative=name.substring(MODEL_NAME.length()+1);
                    if(relative.isEmpty())continue;
                    if(relative.startsWith("/")||relative.contains("../")||relative.contains("..\\")||relative.equals(".."))
                        throw new IOException("Invalid model archive path");
                    File output=new File(unpack,relative);
                    if(!output.getCanonicalPath().startsWith(unpack.getCanonicalPath()+File.separator))
                        throw new IOException("Archive path escapes private directory");
                    if(entry.isDirectory()){if(!output.isDirectory()&&!output.mkdirs())throw new IOException("Unable to create model directory");continue;}
                    File parent=output.getParentFile();
                    if(!parent.isDirectory()&&!parent.mkdirs())throw new IOException("Unable to create model folder");
                    try(OutputStream out=new BufferedOutputStream(new FileOutputStream(output))){
                        byte[] b=new byte[16384];int n;
                        while((n=zin.read(b))!=-1){
                            total+=n;
                            if(total>UNPACK_LIMIT)throw new IOException("Unpacked model exceeds limit");
                            out.write(b,0,n);
                        }
                    }
                    zin.closeEntry();
                }
            }
            if(!new File(unpack,"conf/model.conf").isFile()||
               !new File(unpack,"am/final.mdl").isFile())throw new IOException("Incomplete Vosk model");
            File target=modelDir(context);
            if(target.exists())deleteTree(target);
            if(!unpack.renameTo(target))throw new IOException("Could not activate model");
            notify(callback,"ready");
        } finally {
            archive.delete();
            deleteTree(unpack);
        }
    }

    private static void deleteTree(File f) {
        if(f.isDirectory()){
            File[] children=f.listFiles();
            if(children!=null)for(File child:children)deleteTree(child);
        }
        f.delete();
    }
    private WakeModelInstaller(){}
}
