package de.jarvis.audio;

import java.util.*;
import java.util.function.LongSupplier;

/** Device-monotonic metadata only. No transcript, audio, URL or credentials. */
final class VoiceTrace {
    enum Kind { WAKEWORD, MANUAL, FOLLOWUP, CONTINUOUS }
    enum Status { RUNNING, SUCCESS, NO_REPLY, ERROR, CANCELLED, INTERRUPTED }
    enum Point {
        TRIGGER, ASSIST_START, CONNECT_START, CONNECTED, AUTHENTICATED, PIPELINE_REQUEST,
        RUN_START, STT_START, MIC_READY, SPEECH_START, SPEECH_END, CAPTURE_END,
        INPUT_FIRST_SENT, INPUT_END_SENT, INPUT_QUEUE_DRAINED, STT_END,
        INTENT_START, INTENT_FIRST, INTENT_END, TTS_START, TTS_END, RUN_END,
        JOB_SUBMIT, JOB_ACCEPTED, JOB_RECEIVED, AUDIO_FOCUS, FETCH_START, HTTP_READY,
        FIRST_BYTE, FIRST_PCM, BUFFER_READY, ROUTE_READY, OUTPUT_SUBMITTED,
        OUTPUT_PROGRESS, PLAYBACK_END, SESSION_END
    }
    enum Fact { OUTPUT, ENGINE, OUTPUT_QUALITY, PAUSE_MS, MIC_GAIN, INPUT_BYTES,
        CAPTURED_MS, START_BUFFER_MS, REBUFFERS, UNDERRUNS, WS_QUEUED_BYTES, MIC_PREOPENED }
    static final class Snapshot {
        final String id, error;
        final Kind kind;
        final Status status;
        final long wallMs;
        final Map<Point,Long> points;
        final Map<Fact,String> facts;
        Snapshot(String id, Kind kind, Status status, long wallMs, String error,
                 Map<Point,Long> points, Map<Fact,String> facts) {
            this.id=id;this.kind=kind;this.status=status;this.wallMs=wallMs;this.error=error;
            EnumMap<Point,Long> timing=new EnumMap<>(Point.class);timing.putAll(points);
            EnumMap<Fact,String> metadata=new EnumMap<>(Fact.class);metadata.putAll(facts);
            this.points=Collections.unmodifiableMap(timing);this.facts=Collections.unmodifiableMap(metadata);
        }
        Double between(Point start, Point end) {
            Long a=points.get(start),b=points.get(end);
            return a==null||b==null||b<a?null:(b-a)/1_000_000.0;
        }
        String cohort() {
            return kind+"/"+facts.getOrDefault(Fact.OUTPUT,"unknown")+"/"+
                facts.getOrDefault(Fact.ENGINE,"unknown")+"/pause="+facts.getOrDefault(Fact.PAUSE_MS,"unknown");
        }
    }
    private final String id;
    private final Kind kind;
    private final long origin,wallMs;
    private final LongSupplier clock;
    private final EnumMap<Point,Long> points=new EnumMap<>(Point.class);
    private final EnumMap<Fact,String> facts=new EnumMap<>(Fact.class);
    private Status status=Status.RUNNING;
    private String error="";
    private boolean retired;
    VoiceTrace(String id,Kind kind,LongSupplier clock,long wallMs) {
        this.id=id;this.kind=kind;this.clock=clock;this.origin=clock.getAsLong();this.wallMs=wallMs;
        points.put(Point.TRIGGER,0L);
    }
    static VoiceTrace restore(Snapshot s,LongSupplier clock) {
        VoiceTrace t=new VoiceTrace(s.id,s.kind,clock,s.wallMs);
        t.points.clear();t.points.putAll(s.points);t.facts.putAll(s.facts);
        t.status=s.status==Status.RUNNING?Status.INTERRUPTED:s.status;t.error=s.error;t.retired=true;
        return t;
    }
    synchronized void mark(Point p){if(retired||status!=Status.RUNNING||p!=Point.SPEECH_END&&points.containsKey(p))return;at(p,clock.getAsLong());}
    synchronized void at(Point p,long absoluteNs){
        if(retired||status!=Status.RUNNING||absoluteNs<origin)return;
        long ns=absoluteNs-origin;
        if(ns>600_000_000_000L)return;
        if(p==Point.SPEECH_END)points.put(p,Math.max(points.getOrDefault(p,0L),ns));
        else points.putIfAbsent(p,ns);
    }
    synchronized boolean has(Point p){return points.containsKey(p);}
    synchronized void fact(Fact f,String value){
        if(retired||status!=Status.RUNNING||value==null||!value.matches("[a-z0-9_-]{1,40}"))return;
        facts.put(f,value);
    }
    void fact(Fact f,long n){if(n>=0)fact(f,Long.toString(n));}
    synchronized void add(Fact f,long delta){
        if(retired||status!=Status.RUNNING||delta<0)return;
        long previous=Long.parseLong(facts.getOrDefault(f,"0"));
        facts.put(f,Long.toString(Math.min(100_000_000L,previous+delta)));
    }
    synchronized void finish(Status next,String code){
        if(retired||status!=Status.RUNNING)return;
        mark(Point.SESSION_END);status=next;
        String safe=code==null?"":code.toLowerCase(Locale.ROOT);
        if(next==Status.ERROR)error=safe.matches(
            "(assist_|error_|playback_|audio_|microphone_|tablet_|room_|pipeline_|ha_|websocket_)[a-z0-9_]{1,70}")?safe:"error";
    }
    synchronized void retire(){if(status==Status.RUNNING)status=Status.INTERRUPTED;retired=true;}
    synchronized Snapshot snapshot(){return new Snapshot(id,kind,status,wallMs,error,points,facts);}
    static double percentile(List<Double> data,double quantile){
        if(data.isEmpty()||quantile<0||quantile>1)throw new IllegalArgumentException();
        List<Double> sorted=new ArrayList<>(data);Collections.sort(sorted);
        double index=(sorted.size()-1)*quantile;
        int low=(int)index,high=(int)Math.ceil(index);
        return sorted.get(low)+(sorted.get(high)-sorted.get(low))*(index-low);
    }

    /** Job IDs are only held internally. A job may arrive before submit's HTTP response. */
    static final class Playback {
        private final LongSupplier clock;
        private final EnumMap<Point,Long> pending=new EnumMap<>(Point.class);
        private final EnumMap<Fact,String> facts=new EnumMap<>(Fact.class);
        private VoiceTrace owner;
        private boolean retired;
        Playback(LongSupplier clock){this.clock=clock;}
        synchronized void mark(Point p){
            if(retired)return;
            long now=clock.getAsLong();
            pending.putIfAbsent(p,now);
            if(owner!=null)owner.at(p,now);
        }
        synchronized void fact(Fact f,String v){
            if(retired||v==null||!v.matches("[a-z0-9_-]{1,40}"))return;
            facts.put(f,v);if(owner!=null)owner.fact(f,v);
        }
        void fact(Fact f,long n){if(n>=0)fact(f,Long.toString(n));}
        synchronized boolean bind(VoiceTrace trace){
            if(retired||owner!=null&&owner!=trace)return false;
            owner=trace;
            for(var e:pending.entrySet())trace.at(e.getKey(),e.getValue());
            for(var e:facts.entrySet())trace.fact(e.getKey(),e.getValue());
            return true;
        }
        synchronized void retire(){retired=true;owner=null;pending.clear();facts.clear();}
    }
    /** A silent route warmup never counts as response playback. */
    static final class PresentationGate {
        private long firstFrame=-1;
        private boolean verified,reported;
        void routeVerified(){verified=true;}
        boolean submitted(long first){
            if(firstFrame>=0||first<0)return false;
            firstFrame=first;return true;
        }
        boolean waiting(){return verified&&firstFrame>=0&&!reported;}
        boolean observe(long played){
            if(!waiting()||played<=firstFrame)return false;
            reported=true;return true;
        }
    }
    static final class Store {
        static final int MAX_RUNS=20,MAX_JOBS=32;
        private final LongSupplier clock;
        private final LinkedHashMap<String,VoiceTrace> runs=new LinkedHashMap<>();
        private final LinkedHashMap<String,Playback> jobs=new LinkedHashMap<>();
        private boolean enabled=true;
        Store(LongSupplier clock){this.clock=clock;}
        synchronized VoiceTrace begin(Kind kind,long wallMs){
            VoiceTrace t=new VoiceTrace(UUID.randomUUID().toString(),kind,clock,wallMs);
            if(!enabled){t.retire();return t;}
            runs.put(t.id,t);
            while(runs.size()>MAX_RUNS){String id=runs.keySet().iterator().next();runs.remove(id).retire();}
            return t;
        }
        synchronized void restore(List<Snapshot> snapshots){
            for(Snapshot s:snapshots){if(runs.size()>=MAX_RUNS)break;runs.put(s.id,VoiceTrace.restore(s,clock));}
        }
        synchronized Playback playback(String id){
            if(!id.matches("[a-f0-9]{32}"))throw new IllegalArgumentException("job id");
            Playback p=jobs.get(id);
            if(p==null){
                p=new Playback(clock);
                if(!enabled){p.retire();return p;}
                jobs.put(id,p);
                while(jobs.size()>MAX_JOBS){String first=jobs.keySet().iterator().next();jobs.remove(first).retire();}
            }
            return p;
        }
        synchronized boolean bind(VoiceTrace t,String id){
            return enabled&&runs.get(t.id)==t&&playback(id).bind(t);
        }
        synchronized List<Snapshot> snapshots(){
            List<Snapshot> result=new ArrayList<>();
            for(VoiceTrace t:runs.values())result.add(t.snapshot());
            return result;
        }
        synchronized void enabled(boolean value){
            enabled=value;
            if(!value){for(VoiceTrace t:runs.values())t.retire();for(Playback p:jobs.values())p.retire();jobs.clear();}
        }
        synchronized boolean enabled(){return enabled;}
        synchronized void clear(){
            for(VoiceTrace t:runs.values())t.retire();
            for(Playback p:jobs.values())p.retire();
            runs.clear();jobs.clear();
        }
    }
}
