package de.jarvis.audio;

import java.net.ConnectException;
import java.net.NoRouteToHostException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;

/** Error codes with no server URL, token, or raw exception message. */
final class ConnectionDiagnostics {
    static String status(Throwable e) {
        if(e instanceof java.io.IOException){
            String message=e.getMessage();
            if(message!=null&&message.matches("Room HTTP [1-5][0-9]{2}")){
                String code=message.substring("Room HTTP ".length());
                switch(code){
                    case "401":return "credentials_error|http_401";
                    case "403":return "credentials_error|http_403_room_user";
                    case "404":return "connection_error|http_404_tafa_api";
                    case "409":return "connection_error|http_409_session";
                    case "503":return "connection_error|http_503_not_ready";
                    default:return "connection_error|http_"+code;
                }
            }
        }
        if(e instanceof javax.net.ssl.SSLException)return "connection_error|tls_certificate";
        if(e instanceof UnknownHostException)return "connection_error|dns_failed";
        if(e instanceof SocketTimeoutException)return "connection_error|timeout";
        if(e instanceof NoRouteToHostException)return "connection_error|network_route";
        if(e instanceof ConnectException)return "connection_error|host_refused";
        if(e instanceof java.net.ProtocolException)return "connection_error|http_protocol";
        if(e instanceof java.io.EOFException)return "connection_error|http_incomplete";
        if(e instanceof java.io.IOException)return "connection_error|io_failure";
        return "connection_error|"+e.getClass().getSimpleName();
    }
    private ConnectionDiagnostics(){}
}
