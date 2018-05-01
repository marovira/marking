import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

public class Test
{
    public static void main(String[] args) 
    {
        try
        {
            File infile = new File("test.txt");
            FileReader filereader = new FileReader(infile);
            BufferedReader bufferedreader = new BufferedReader(filereader);
            StringBuffer stringbuffer = new StringBuffer();
            String line;
            while ((line = bufferedreader.readLine()) != null)
            {
                stringbuffer.append(line);
                stringbuffer.append("\n");
            }
            filereader.close();
            System.out.println("Some random text.");
            System.out.println("contents of file:");
            System.out.println(stringbuffer.toString());
            System.out.println("Exiting...");
        }
        catch (IOException e)
        {
            e.printStackTrace();
        }
    }
}
