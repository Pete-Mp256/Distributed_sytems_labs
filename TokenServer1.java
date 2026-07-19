import java.io.*;
import java.net.*;

public class TokenServer1 {
    public static void main(String agrs[]) throws Exception {

        while (true) {
            Server sr = new Server();
            sr.recPort(8000);
            sr.recData();
        }
    }
}

class Server {

    boolean hasToken = false;
    boolean sendData = false;
    int recport;

    void recPort(int recport) {
        this.recport = recport;
    }

    void recData() throws Exception {
        byte buff[] = new byte[256];
        DatagramSocket ds;
        DatagramPacket dp;
        String str;

        ds = new DatagramSocket(recport);
        dp = new DatagramPacket(buff, buff.length);
        ds.receive(dp);
        ds.close();

        str = new String(dp.getData(), 0, dp.getLength());
        System.out.println("The message is " + str);
    }
}
