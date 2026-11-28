package com.model;

public class User extends Entity {
    private String email;
    private String fullName;

    public User(int id, String email, String fullName) {
        super(id);
        this.email = email;
        this.fullName = fullName;
    }

    @Override
    public void show() {
        System.out.println(fullName + " <" + email + ">");
    }
}
