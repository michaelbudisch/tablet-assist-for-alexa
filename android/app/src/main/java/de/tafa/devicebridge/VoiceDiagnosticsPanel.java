package de.tafa.devicebridge;

import android.app.Activity;
import android.content.*;
import android.view.View;
import android.widget.*;
import java.text.DateFormat;
import java.util.*;
import static de.tafa.devicebridge.VoiceTrace.Point.*;

final class VoiceDiagnosticsPanel {
    private final Activity activity;
    private final Spinner selector;
    private final TextView summary,details,primary;
    private final Locale locale;
    private final String[] points,kinds,statuses,metrics;
    private List<VoiceTrace.Snapshot> visible=new ArrayList<>();
    private List<String> labels=new ArrayList<>();
    private boolean updating,followLatest=true;
    private String selectedId="";
    private final VoiceTrace.Point[][] intervals={
        {SPEECH_END,OUTPUT_PROGRESS},{TRIGGER,OUTPUT_PROGRESS},{TRIGGER,MIC_READY},
        {SPEECH_START,SPEECH_END},{SPEECH_END,CAPTURE_END},{ASSIST_START,STT_START},
        {INPUT_FIRST_SENT,INPUT_END_SENT},{INPUT_END_SENT,STT_END},
        {INTENT_START,INTENT_END},{TTS_START,TTS_END},{JOB_SUBMIT,JOB_RECEIVED},
        {FETCH_START,FIRST_BYTE},{FIRST_BYTE,FIRST_PCM},{FIRST_PCM,BUFFER_READY},
        {BUFFER_READY,ROUTE_READY},{ROUTE_READY,OUTPUT_PROGRESS},
        {OUTPUT_PROGRESS,PLAYBACK_END},{PLAYBACK_END,SESSION_END}
    };
    VoiceDiagnosticsPanel(Activity activity){
        this.activity=activity;VoiceDiagnostics.init(activity);
        locale=activity.getResources().getConfiguration().getLocales().get(0);
        points=activity.getResources().getStringArray(R.array.flow_point_labels);
        kinds=activity.getResources().getStringArray(R.array.flow_kinds);
        statuses=activity.getResources().getStringArray(R.array.flow_statuses);
        metrics=activity.getResources().getStringArray(R.array.flow_metric_labels);
        selector=activity.findViewById(R.id.flow_runs);
        summary=activity.findViewById(R.id.flow_summary);details=activity.findViewById(R.id.flow_details);
        primary=activity.findViewById(R.id.flow_primary);
        CheckBox recording=activity.findViewById(R.id.flow_recording);
        recording.setChecked(VoiceDiagnostics.enabled());
        recording.setOnCheckedChangeListener((v,on)->{VoiceDiagnostics.enabled(activity,on);refresh();});
        selector.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(AdapterView<?> parent){}
            public void onItemSelected(AdapterView<?> parent,View view,int position,long id){
                if(updating||position>=visible.size())return;
                selectedId=visible.get(position).id;followLatest=position==0;showDetails(visible.get(position));
            }
        });
        activity.findViewById(R.id.flow_clear).setOnClickListener(v->{
            VoiceDiagnostics.clear();selectedId="";followLatest=true;refresh();
        });
        activity.findViewById(R.id.flow_copy).setOnClickListener(v->{
            activity.getSystemService(android.content.ClipboardManager.class).setPrimaryClip(
                ClipData.newPlainText("TAFA native flow",VoiceDiagnostics.export()));
            Toast.makeText(activity,R.string.flow_copied,Toast.LENGTH_SHORT).show();
        });
        activity.findViewById(R.id.flow_share).setOnClickListener(v->{
            Intent share=new Intent(Intent.ACTION_SEND).setType("text/plain")
                .putExtra(Intent.EXTRA_SUBJECT,"TAFA Device Bridge "+BuildConfig.VERSION_NAME+" diagnostics")
                .putExtra(Intent.EXTRA_TEXT,VoiceDiagnostics.export());
            activity.startActivity(Intent.createChooser(share,activity.getString(R.string.flow_share)));
        });
    }
    void refresh(){
        if(!selector.isShown())return;
        List<VoiceTrace.Snapshot> next=VoiceDiagnostics.snapshots();Collections.reverse(next);visible=next;
        List<String> nextLabels=new ArrayList<>();
        for(VoiceTrace.Snapshot s:next)nextLabels.add(DateFormat.getTimeInstance(DateFormat.MEDIUM,locale).format(new Date(s.wallMs))+
            " · "+kinds[s.kind.ordinal()]+" · "+statuses[s.status.ordinal()]);
        int selected=0;
        if(!followLatest)for(int i=0;i<next.size();i++)if(next.get(i).id.equals(selectedId))selected=i;
        if(!nextLabels.equals(labels)){
            labels=nextLabels;updating=true;
            selector.setAdapter(BridgeChoices.create(activity,nextLabels.isEmpty()?
                Collections.singletonList(activity.getString(R.string.flow_empty)):nextLabels));
            selector.setSelection(selected);updating=false;
        }
        if(next.isEmpty()){set(details,activity.getString(R.string.flow_empty));set(primary,activity.getString(R.string.flow_primary,"—"));}
        else {selectedId=next.get(selected).id;showDetails(next.get(selected));}
        Map<String,List<Double>> groups=new LinkedHashMap<>();
        Map<String,String> cohortLabels=new LinkedHashMap<>();
        for(VoiceTrace.Snapshot s:next){
            Double duration=s.between(SPEECH_END,OUTPUT_PROGRESS);
            if(s.status==VoiceTrace.Status.SUCCESS&&duration!=null)
                groups.computeIfAbsent(s.cohort(),k->new ArrayList<>()).add(duration);
            cohortLabels.put(s.cohort(),kinds[s.kind.ordinal()]+" · "+
                s.facts.getOrDefault(VoiceTrace.Fact.OUTPUT,"—")+" · "+
                s.facts.getOrDefault(VoiceTrace.Fact.ENGINE,"—")+" · "+
                s.facts.getOrDefault(VoiceTrace.Fact.PAUSE_MS,"—")+" ms · build "+
                s.facts.getOrDefault(VoiceTrace.Fact.BUILD_CODE,"—"));
        }
        StringBuilder text=new StringBuilder(activity.getString(R.string.flow_statistics));
        for(var entry:groups.entrySet()){
            List<Double> values=entry.getValue();
            text.append("\n").append(cohortLabels.get(entry.getKey())).append(" · n=").append(values.size())
                .append(" · p50 ").append(ms(VoiceTrace.percentile(values,0.5)))
                .append(" · p95 ").append(ms(VoiceTrace.percentile(values,0.95)));
        }
        if(groups.isEmpty())text.append("\n").append(activity.getString(R.string.flow_no_statistics));
        set(summary,text.toString());
    }
    private String ms(Double n){
        return n==null?"—":String.format(activity.getResources().getConfiguration().getLocales().get(0),"%.1f ms",n);
    }
    private void showDetails(VoiceTrace.Snapshot s){
        set(primary,activity.getString(R.string.flow_primary,ms(s.between(SPEECH_END,OUTPUT_PROGRESS))));
        StringBuilder text=new StringBuilder(DateFormat.getDateTimeInstance(DateFormat.MEDIUM,DateFormat.MEDIUM,locale).format(new Date(s.wallMs)));
        text.append(" · ").append(s.id.substring(0,8)).append("\n").append(kinds[s.kind.ordinal()])
            .append(" · ").append(statuses[s.status.ordinal()]);
        if(!s.error.isEmpty())text.append(" · ").append(s.error);
        for(int i=0;i<intervals.length;i++)
            text.append("\n").append(metrics[i]).append(": ").append(ms(s.between(intervals[i][0],intervals[i][1])));
        text.append("\n\n").append(activity.getString(R.string.flow_timeline));
        List<Map.Entry<VoiceTrace.Point,Long>> timeline=new ArrayList<>(s.points.entrySet());
        timeline.sort(Map.Entry.comparingByValue());
        for(var point:timeline)text.append("\n+").append(ms(point.getValue()/1_000_000.0))
            .append("  ").append(points[point.getKey().ordinal()]);
        if(!s.facts.isEmpty()){
            text.append("\n\n").append(activity.getString(R.string.flow_parameters));
            for(var fact:s.facts.entrySet())text.append("\n")
                .append(fact.getKey().name().toLowerCase(Locale.ROOT)).append(" = ").append(fact.getValue());
        }
        set(details,text.toString());
    }
    private void set(TextView view,String value){if(!view.getText().toString().equals(value))view.setText(value);}
}
