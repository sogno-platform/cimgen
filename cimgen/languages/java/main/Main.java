package cim4j.main;

import java.util.ArrayList;
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
        System.out.println("\nRead RDF files and write the data to RDF files separated by profiles.\n");
        System.out.println("Usage: java -jar cim4j.jar <rdf_file>  [<rdf_file>  ...] <output_path_stem>");
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

        checkArgs(inputFiles);

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
        try {
            var rdfReader = new RdfReader();
            return rdfReader.read(inputFiles);
        } catch (Exception ex) {
            LOG.error("Failed to convert RDF files to CIM", ex);
            return null;
        }
    }

    /**
     * Write the CIM data to RDF files separated by profiles.
     *
     * @param pathStem Stem of the output files
     *                 (also used as stem of the model IDs)
     * @param cimData  CIM data as map of rdfid to CIM object
     */
    public static void writeRdf(String pathStem, Map<String, BaseClass> cimData) {
        try {
            var writer = new RdfWriter();
            writer.addCimData(cimData);
            var profileFileMap = writer.write(pathStem, pathStem, writer.getClassProfileMap());
            int count = 0;
            for (var profile : profileFileMap.keySet()) {
                ++count;
                LOG.info(String.format("CIM outputfile %d: %s", count, profileFileMap.get(profile)));
            }
        } catch (Exception ex) {
            LOG.error("Failed to write CIM data to a RDF file", ex);
            return;
        }
    }

    private static void checkArgs(List<String> inputFiles) {
        for (String inputFile : inputFiles) {
            if (!isRdfFile(inputFile)) {
                printUsageAndExit(inputFile + " is not a rdf file");
            }
        }
    }

    private static boolean isRdfFile(String fileName) {
        String file = fileName.toLowerCase();
        return file.endsWith(".rdf") || file.endsWith(".xml");
    }
}
