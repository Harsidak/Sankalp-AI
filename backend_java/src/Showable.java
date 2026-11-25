// An interface is a promise: any class that implements Showable MUST have a show() method.
// Main can then call show() on a User, Habit, Tag... without caring which one it is.
public interface Showable {
    void show();
}
