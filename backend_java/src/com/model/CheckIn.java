package com.model;

public class CheckIn extends Entity {
    private String date;
    private int mood;
    private int energy;
    private String note;

    public CheckIn(int id, String date, int mood, int energy, String note) {
        super(id);
        this.date = date;
        this.mood = mood;
        this.energy = energy;
        this.note = note;
    }

    @Override
    public void show() {
        String bar = "";
        for (int i = 0; i < mood; i++) {
            bar = bar + "#";
        }
        System.out.printf("%s  mood %-5s %d/5   energy %d/5   %s%n", date, bar, mood, energy, note);
    }
}
