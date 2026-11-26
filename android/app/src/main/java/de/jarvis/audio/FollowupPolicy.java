package de.jarvis.audio;

/** Local hard ceiling; Home Assistant may only reduce it. Counts additional questions. */
final class FollowupPolicy {
    static final String LOCAL_LIMIT = "local_followup_limit";
    private FollowupPolicy() {}
    static int localLimit(int configured) {
        return Math.max(0, Math.min(10, configured));
    }
    static int effectiveLimit(int local, int remote) {
        int ceiling = localLimit(local);
        return remote == -1 ? ceiling : Math.min(ceiling, Math.max(0, remote));
    }
    static boolean shouldContinue(boolean answered, int completedFollowups, int limit) {
        return answered && completedFollowups >= 0 && completedFollowups < localLimit(limit);
    }
}
