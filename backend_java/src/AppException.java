// Our own exception, used for mistakes the USER makes
// (for example "no habit with that number"), as opposed to SQLException which is a database problem.
public class AppException extends Exception {

    public AppException(String message) {
        super(message);
    }
}
