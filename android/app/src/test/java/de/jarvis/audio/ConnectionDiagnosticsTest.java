package de.jarvis.audio;
import org.junit.Test;
import static org.junit.Assert.*;
import java.io.IOException;
import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import javax.net.ssl.SSLHandshakeException;

public class ConnectionDiagnosticsTest {
    @Test public void roomErrorsAreActionable() {
        assertEquals("connection_error|http_404_tafa_api",ConnectionDiagnostics.status(new IOException("Room HTTP 404")));
        assertEquals("connection_error|http_409_session",ConnectionDiagnostics.status(new IOException("Room HTTP 409")));
        assertEquals("connection_error|http_503_not_ready",ConnectionDiagnostics.status(new IOException("Room HTTP 503")));
        assertEquals("credentials_error|http_403_room_user",ConnectionDiagnostics.status(new IOException("Room HTTP 403")));
        assertEquals("credentials_error|http_401",ConnectionDiagnostics.status(new IOException("Room HTTP 401")));
        assertEquals("connection_error|http_400",ConnectionDiagnostics.status(new IOException("Room HTTP 400")));
    }
    @Test public void networkErrorsNeverLeakSecrets() {
        assertEquals("connection_error|dns_failed",ConnectionDiagnostics.status(new UnknownHostException("private.test")));
        assertEquals("connection_error|timeout",ConnectionDiagnostics.status(new SocketTimeoutException("secret")));
        assertEquals("connection_error|host_refused",ConnectionDiagnostics.status(new ConnectException("private")));
        assertEquals("connection_error|tls_certificate",ConnectionDiagnostics.status(new SSLHandshakeException("private cert")));
        assertEquals("connection_error|io_failure",ConnectionDiagnostics.status(new IOException("Bearer SECRET at https://private.test")));
    }
}
