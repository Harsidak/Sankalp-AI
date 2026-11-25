// One row of the habits table, plus two facts we calculate (done today? streak?).
public class Habit extends Entity {

    private String name;
    private boolean doneToday;
    private int streak;

    public Habit(int id, String name) {
        super(id);
        this.name = name;
    }

    // setters: the manager fills these in after it has calculated them
    public void setDoneToday(boolean doneToday) {
        this.doneToday = doneToday;
    }

    public void setStreak(int streak) {
        this.streak = streak;
    }

    @Override
    public void show() {
        String box = doneToday ? "[x]" : "[ ]";
        System.out.println(getId() + ". " + box + " " + name + "   (streak: " + streak + " days)");
    }
}
