package cim4j.main;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import cim4j.BaseClass;
import cim4j.Logging;
import cim4j.utils.RdfReader;
import cim4j.utils.RdfWriter;

/**
 * Main class of the cim4j application.
 */
public final class Main {

    private static final Logging LOG = Logging.getLogger(Main.class);

    // Private dummy constructor - prevent to instantiate the class at all
    private Main() {
    }

    private static void printUsageAndExit(String aError) {
        if (!aError.isEmpty()) {
            System.out.println("\nError: " + aError);
        }
        System.out.println("\nRead rdf files and write the data to one rdf file.\n");
        System.out.println("Usage: java -jar cim4j.jar <rdf_file>  [<rdf_file>  ...] <rdf_file>");
        System.exit(2);
    }

    /**
     * Main function of the cim4j application.
     */
    public static void main(String[] aArgs) {
        if (aArgs.length < 2) {
            printUsageAndExit("too few arguments");
        }

        List<String> inputFiles = new ArrayList<>();
        for (int idx = 0; idx < aArgs.length - 1; ++idx) {
            inputFiles.add(aArgs[idx]);
        }
        String outputFile = aArgs[aArgs.length - 1];

        checkArgs(inputFiles, outputFile);

        readRdfWriteRdf(inputFiles, outputFile);
    }

    /**
     * Read cim data from rdf files, write the data to a rdf file.
     *
     * @param inputFiles list of paths of files to read
     * @param outputFile path of file to write
     */
    public static void readRdfWriteRdf(List<String> inputFiles, String outputFile) {
        var cimData = readRdf(inputFiles);
        if (cimData != null) {
            writeRdf(outputFile, cimData);
        }
    }

    /**
     * Read the cim data from rdf files.
     *
     * @param inputFiles list of paths of files to read
     * @return cim data as map of rdfid to cim object
     */
    public static Map<String, BaseClass> readRdf(List<String> inputFiles) {
        var allCimData = new LinkedHashMap<String, BaseClass>();
        try {
            for (String rdfFile : inputFiles) {
                LOG.info("Read RDF file: " + rdfFile);
                var cimData = RdfReader.read(rdfFile);
                allCimData.putAll(cimData);
            }
        } catch (Exception ex) {
            LOG.error("Failed to convert RDF files to CIM", ex);
            return null;
        }
        return allCimData;
    }

    /**
     * Write cim data to a rdf file.
     *
     * @param outputFile path of file to write
     * @param cimData    cim data as map of rdfid to cim object
     */
    public static void writeRdf(String outputFile, Map<String, BaseClass> cimData) {
        try {
            var writer = new RdfWriter();
            writer.addCimData(cimData);
            writer.write(outputFile);
        } catch (Exception ex) {
            LOG.error("Failed to write CIM data to a RDF file", ex);
            return;
        }
    }

    private static void checkArgs(List<String> inputFiles, String outputFile) {
        for (String inputFile : inputFiles) {
            if (!isRdfFile(inputFile)) {
                printUsageAndExit(inputFile + " is not a rdf file");
            }
        }
        if (!isRdfFile(outputFile)) {
            printUsageAndExit(outputFile + " is not a rdf file");
        }
    }

    private static boolean isRdfFile(String fileName) {
        String file = fileName.toLowerCase();
        return file.endsWith(".rdf") || file.endsWith(".xml");
    }
}
