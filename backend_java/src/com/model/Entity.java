package com.model;

// Parent of every class that is a row in a table. The id lives here once.
// abstract = we can only create its children (Habit, Tag...), never new Entity().
public abstract class Entity implements Showable {
    private int id; // private = encapsulation

    public Entity(int id) {
        this.id = id;
    }

    public int getId() {
        return id;
    }
}
