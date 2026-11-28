package de.tafa.devicebridge;

import java.text.Normalizer;
import java.util.Locale;

/** Pure, testable phrase matching. No microphone or network access. */
final class WakeWordMatcher {
    static final String[] OPTIONS = {"hey_jarvis", "jarvis", "alexa", "all"};
    private WakeWordMatcher() {}

    static String normalize(String input) {
        String value = Normalizer.normalize(input == null ? "" : input, Normalizer.Form.NFD)
            .replaceAll("\\p{M}+", "").toLowerCase(Locale.ROOT);
        return value.replaceAll("[^a-z0-9 ]+", " ").replaceAll("\\s+", " ").trim();
    }

    static String matched(String transcript, String selection) {
        String phrase = " " + normalize(transcript) + " ";
        String chosen = selection == null ? "hey_jarvis" : selection;
        boolean all = "all".equals(chosen);
        // The longer phrase is checked first so that it is not lost to Jarvis.
        if ((all || "hey_jarvis".equals(chosen)) &&
                (phrase.contains(" hey jarvis ") || phrase.contains(" hey jarwis ") ||
                 phrase.contains(" hei jarvis ") || phrase.contains(" hey djarvis "))) {
            return "Hey Jarvis";
        }
        if ((all || "jarvis".equals(chosen)) &&
                (phrase.contains(" jarvis ") || phrase.contains(" jarwis ") ||
                 phrase.contains(" djarvis "))) {
            return "Jarvis";
        }
        if ((all || "alexa".equals(chosen)) && phrase.contains(" alexa ")) {
            return "Alexa";
        }
        return null;
    }
}
