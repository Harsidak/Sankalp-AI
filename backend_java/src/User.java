// One row of the users table.
public class User extends Entity {

    private String email;
    private String fullName;

    public User(int id, String email, String fullName) {
        super(id); // call the parent constructor to store the id
        this.email = email;
        this.fullName = fullName;
    }

    public String getFullName() {
        return fullName;
    }

    @Override
    public void show() {
        System.out.println(fullName + " <" + email + ">");
    }
}
