import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

public class Test
{
    public static void main(String[] args)
    {
        File inFile = new File("test.txt");
        FileReader fileReader = new FileReader(inFile);
        BufferedReader bufferedReader = new BufferedReader(fileReader);
        StringBuffer stringBuffer = new StringBuffer();
        String line;
        while ((line = bufferedReader.readLine()) != null)
        {
            stringBuffer.append(line);
            stringBuffer.append("\n");
        }
        fileReader.close();
        System.out.println("Contents of file:");
        System.out.println(stringBuffer.toString());
    }
}
