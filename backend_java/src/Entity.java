// Parent class of everything that is stored as a row in a table.
// Every row has an id, so the id lives here once instead of being repeated in every class.
// "abstract" = you cannot write new Entity(); you can only create its children (Habit, Tag...).
public abstract class Entity implements Showable {

    private int id; // private = only this class can touch it directly (encapsulation)

    public Entity(int id) {
        this.id = id;
    }

    public int getId() {
        return id;
    }
}
