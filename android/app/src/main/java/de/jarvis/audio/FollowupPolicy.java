package de.jarvis.audio;

/** Home Assistant is the only authority for per-tablet follow-up count.
 *  -1 = unlimited until a silent/no-answer session, 0 = disabled.
 *  All other values count additional questions after the first response.
 */
final class FollowupPolicy {
    private FollowupPolicy() {}
    static boolean shouldContinue(boolean answered,int completedFollowups,int limit){
        if(!answered||completedFollowups<0)return false;
        return limit==-1 || (limit>0&&completedFollowups<limit);
    }
}
