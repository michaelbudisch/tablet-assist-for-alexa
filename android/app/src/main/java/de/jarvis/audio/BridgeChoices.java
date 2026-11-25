package de.jarvis.audio;

import android.content.Context;
import android.widget.ArrayAdapter;
import java.util.List;

/** App-owned layouts keep selected values and popup rows legible in the dark theme. */
final class BridgeChoices {
    private BridgeChoices() {}
    static <T> ArrayAdapter<T> create(Context context, List<T> values) {
        ArrayAdapter<T> adapter = new ArrayAdapter<>(context, R.layout.spinner_selected, values);
        adapter.setDropDownViewResource(R.layout.spinner_dropdown);
        return adapter;
    }
}
