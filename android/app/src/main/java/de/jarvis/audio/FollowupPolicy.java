package de.jarvis.audio;

/** Follow-ups require HA's invitation and a local per-tablet opt-in. */
final class FollowupPolicy {
    static final String LOCAL_LIMIT = "local_followup_limit";
    private FollowupPolicy() {}

    static int localLimit(int configured) {
        if(configured==-1)return -1;
        return Math.max(0,Math.min(100,configured));
    }
    static int effectiveLimit(int local,int remote) {
        int ceiling=localLimit(local);
        if(remote==-1)return ceiling; // HA imposes no extra ceiling
        int ha=Math.max(0,Math.min(100,remote));
        return ceiling==-1?ha:Math.min(ceiling,ha);
    }
    static final String LOCAL_TIMEOUT_MS="local_followup_timeout_ms";
    static final int DEFAULT_TIMEOUT_MS=3000;
    static int timeoutMs(int configured){
        return Math.max(2000,Math.min(6000,configured));
    }
    static boolean shouldContinue(boolean answered,boolean invited,int completedFollowups,int limit){
        return answered&&invited&&completedFollowups>=0&&
            (limit==-1||completedFollowups<localLimit(limit));
    }
}
