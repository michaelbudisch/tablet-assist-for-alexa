package de.tafa.devicebridge;

/** Confirmation threshold for consecutive Vosk recognition hypotheses. */
final class WakeTriggerGate {
    private String last;
    private int confirmations;

    synchronized boolean confirm(String phrase,int required){
        if(phrase==null||phrase.isEmpty()){
            reset();return false;
        }
        if(phrase.equals(last))confirmations++;
        else{last=phrase;confirmations=1;}
        return confirmations>=Math.max(1,Math.min(3,required));
    }

    synchronized void reset(){last=null;confirmations=0;}
}
