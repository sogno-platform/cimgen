package cim4j;

import java.time.LocalDateTime;

// import org.apache.logging.log4j.LogManager;
// import org.apache.logging.log4j.Logger;

/**
 * Wrapper to log with real logger and/or by System.out.println.
 *
 * To switch from System.out.println to real logger uncomment the commented
 * lines and set printlnEnabled = false.
 */
public class Logging {
    public enum Level {
        fatal,
        error,
        warn,
        info,
        debug,
        trace
    }

    private static Level defaultLevel = Level.error;
    private Level level;
    private String className;
    // private Logger log4jLogger;
    private static boolean log4jEnabled = true;
    private static boolean printlnEnabled = true;

    private Logging(final Class<?> clazz, Level logLevel) {
        level = logLevel;
        className = clazz.getName();
        // log4jLogger = LogManager.getLogger(clazz);
    }

    private void log(Level logLevel, String message) {
        if (printlnEnabled && logLevel.compareTo(level) <= 0) {
            System.out.println(LocalDateTime.now() + " " + className + " " + logLevel + ": " + message);
        }
    }

    /**
     * Returns a Logger using the fully qualified name of the Class as the Logger
     * name.
     *
     * @param clazz The Class whose name should be used as the Logger name.
     */
    public static Logging getLogger(final Class<?> clazz) {
        return new Logging(clazz, defaultLevel);
    }

    /**
     * Returns a Logger using the fully qualified name of the Class as the Logger
     * name.
     *
     * @param clazz The Class whose name should be used as the Logger name.
     * @param level Log level.
     */
    public static Logging getLogger(final Class<?> clazz, Level level) {
        return new Logging(clazz, level);
    }

    /**
     * Is logging enabled?
     *
     * @return logging enabled?
     */
    public static boolean isEnabled() {
        // return log4jEnabled;
        return printlnEnabled;
    }

    /**
     * Enable or disable logging - for unit tests.
     *
     * @param enabled logging enabled
     */
    public static void setEnabled(boolean enabled) {
        log4jEnabled = enabled;
        printlnEnabled = enabled;
    }

    /**
     * Returns the default log level.
     *
     * @return default log level
     */
    public static Level getDefaultLogLevel() {
        return defaultLevel;
    }

    /**
     * Sets the default log level.
     *
     * @param level Log level.
     */
    public static void setDefaultLogLevel(Level level) {
        defaultLevel = level;
    }

    /**
     * Logs a message object with the FATAL level.
     *
     * @param message the message string to log.
     */
    public void fatal(String message) {
        if (log4jEnabled) {
            // log4jLogger.fatal(message);
        }
        log(Level.fatal, message);
    }

    /**
     * Logs a message object with the ERROR level.
     *
     * @param message the message string to log.
     */
    public void error(String message) {
        if (log4jEnabled) {
            // log4jLogger.error(message);
        }
        log(Level.error, message);
    }

    /**
     * Logs a message object with the WARN level.
     *
     * @param message the message string to log.
     */
    public void warn(String message) {
        if (log4jEnabled) {
            // log4jLogger.warn(message);
        }
        log(Level.warn, message);
    }

    /**
     * Logs a message object with the INFO level.
     *
     * @param message the message string to log.
     */
    public void info(String message) {
        if (log4jEnabled) {
            // log4jLogger.info(message);
        }
        log(Level.info, message);
    }

    /**
     * Logs a message object with the DEBUG level.
     *
     * @param message the message string to log.
     */
    public void debug(String message) {
        if (log4jEnabled) {
            // log4jLogger.debug(message);
        }
        log(Level.debug, message);
    }

    /**
     * Logs a message object with the TRACE level.
     *
     * @param message the message string to log.
     */
    public void trace(String message) {
        if (log4jEnabled) {
            // log4jLogger.trace(message);
        }
        log(Level.trace, message);
    }

    /**
     * Logs a message object with the FATAL level including the stack trace of the
     * {@link Throwable} <code>throwable</code> passed as parameter.
     *
     * @param message   the message CharSequence to log.
     * @param throwable the {@code Throwable} to log, including its stack trace.
     */
    public void fatal(String message, Throwable throwable) {
        if (log4jEnabled) {
            // log4jLogger.fatal(message, throwable);
        }
        log(Level.fatal, message + " Exception:" + throwable.getMessage());
    }

    /**
     * Logs a message object with the ERROR level including the stack trace of the
     * {@link Throwable} <code>throwable</code> passed as parameter.
     *
     * @param message   the message CharSequence to log.
     * @param throwable the {@code Throwable} to log, including its stack trace.
     */
    public void error(String message, Throwable throwable) {
        if (log4jEnabled) {
            // log4jLogger.error(message, throwable);
        }
        log(Level.error, message + " Exception:" + throwable.getMessage());
    }

    /**
     * Logs a message object with the WARN level including the stack trace of the
     * {@link Throwable} <code>throwable</code> passed as parameter.
     *
     * @param message   the message CharSequence to log.
     * @param throwable the {@code Throwable} to log, including its stack trace.
     */
    public void warn(String message, Throwable throwable) {
        if (log4jEnabled) {
            // log4jLogger.warn(message, throwable);
        }
        log(Level.warn, message + " Exception:" + throwable.getMessage());
    }
}
