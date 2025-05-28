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

    private static Logging LOG = Logging.getLogger(Main.class);

    // Private dummy constructor - prevent to instantiate the class at all
    private Main() {
    }

    private static void printUsageAndExit(String error) {
        if (!error.isEmpty()) {
            System.out.println("\nError: " + error);
        }
        System.out.println("\nRead RDF files and write the data to RDF files separated by profiles.\n");
        System.out.println("Usage: java -jar cim4j.jar [--log-level <level>] <rdf_file> [<rdf_file> ...]" +
                " <output_path_stem>");
        System.out.println("       --log-level <level>  Log level (fatal, error, warn, info, debug, trace)");
        System.out.println("                            Default log level: error");
        System.out.println("       <rdf_file> ...       Input files with CIM/CGMES data");
        System.out.println("       <output_path_stem>   Stem of the output files" +
                " (<output_path_stem>_<profile_name>.xml)");
        System.exit(2);
    }

    /**
     * Main function of the cim4j application.
     */
    public static void main(String[] args) {
        int offset = 0;
        if (args.length >= 2 && args[0].equals("--log-level")) {
            Logging.Level level = Logging.getDefaultLogLevel();
            try {
                level = Logging.Level.valueOf(args[1]);
            } catch (IllegalArgumentException ex) {
                printUsageAndExit("unknown log level: " + args[1]);
            }
            if (!level.equals(Logging.getDefaultLogLevel())) {
                Logging.setDefaultLogLevel(level);
                LOG = Logging.getLogger(Main.class);
            }
            offset += 2;
        }

        if (args.length < offset + 2) {
            printUsageAndExit("too few arguments");
        }

        List<String> inputFiles = new ArrayList<>();
        for (int idx = offset; idx < args.length - 1; ++idx) {
            inputFiles.add(args[idx]);
        }
        String outputFile = args[args.length - 1];

        checkArgs(inputFiles);

        readRdfWriteRdf(inputFiles, outputFile);

        LOG.info(String.format("Total allocated memory: %d of %d MByte",
                Runtime.getRuntime().totalMemory() / (1024 * 1024), Runtime.getRuntime().maxMemory() / (1024 * 1024)));
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
            int count = 0;
            for (var file : inputFiles) {
                ++count;
                LOG.info(String.format("CIM inputfile %d: %s", count, file));
            }
            var cimData = rdfReader.read(inputFiles);
            LOG.info(String.format("Read %d inputfiles", count));
            return cimData;
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
            LOG.info(String.format("Written %d outputfiles", count));
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
