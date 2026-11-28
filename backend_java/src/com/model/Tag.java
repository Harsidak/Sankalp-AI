package com.model;

public class Tag extends Entity {
    private String name;
    private int entryCount;

    public Tag(int id, String name, int entryCount) {
        super(id);
        this.name = name;
        this.entryCount = entryCount;
    }

    @Override
    public void show() {
        System.out.println(getId() + ". " + name + "  (" + entryCount + " entries)");
    }
}
