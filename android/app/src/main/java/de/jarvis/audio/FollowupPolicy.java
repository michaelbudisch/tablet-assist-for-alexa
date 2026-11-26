package de.jarvis.audio;

/** Explicit per-tablet follow-ups; -1 is unlimited until silence/error/mute. */
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
    static boolean shouldContinue(boolean answered,int completedFollowups,int limit) {
        return answered&&completedFollowups>=0&&
            (limit==-1||completedFollowups<localLimit(limit));
    }
}
