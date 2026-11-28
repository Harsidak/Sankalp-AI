package com.model;

public class JournalEntry extends Entity {
    private String title;
    private String content;
    private String createdAt;
    private String tags; // tag names as one text, e.g. "study, health"

    public JournalEntry(int id, String title, String content, String createdAt, String tags) {
        super(id);
        this.title = title;
        this.content = content;
        this.createdAt = createdAt;
        this.tags = tags;
    }

    public String getTitle() {
        return title;
    }

    public String getContent() {
        return content;
    }

    public String getCreatedAt() {
        return createdAt;
    }

    public String getTags() {
        return tags;
    }

    @Override
    public void show() {
        System.out.println(getId() + ". " + createdAt + "  " + title + "  [" + tags + "]");
    }

    public void showFull() {
        show();
        System.out.println();
        System.out.println(content);
    }
}
