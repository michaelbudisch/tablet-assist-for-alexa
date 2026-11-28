package de.tafa.devicebridge;

import android.content.Context;
import android.content.res.Configuration;
import android.os.LocaleList;
import java.util.Locale;

final class AppLanguage {
    static Context wrap(Context base) {
        String saved = base.getSharedPreferences(MainActivity.PREF, 0).getString("ui_language", "");
        Locale locale = saved.isEmpty() ? base.getResources().getConfiguration().getLocales().get(0)
                : Locale.forLanguageTag(saved);
        if (!locale.getLanguage().equals("de")) locale = Locale.ENGLISH;
        else locale = Locale.GERMAN;
        Configuration config = new Configuration(base.getResources().getConfiguration());
        config.setLocales(new LocaleList(locale));
        return base.createConfigurationContext(config);
    }

    static String error(Context context, Exception error) {
        String code = error.getMessage() == null ? "" : error.getMessage();
        int id;
        switch (code) {
            case "invalid_address": id = R.string.invalid_address; break;
            case "http_lan_only": id = R.string.http_lan_only; break;
            case "http_consent_required": id = R.string.http_consent_required; break;
            case "invalid_qr_token": id = R.string.invalid_qr_token; break;
            case "token_required": id = R.string.token_required; break;
            case "token_server_changed": id = R.string.token_server_changed; break;
            default: id = R.string.setup_error;
        }
        return context.getString(id);
    }

    private AppLanguage() {}
}
