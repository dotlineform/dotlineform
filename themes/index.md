---
layout: default
title: Curated works
permalink: /works-notes/
---

<h1 class="visually-hidden">Curated works</h1>

{% assign works_notes = site.works_notes %}

{% if works_notes and works_notes != empty %}
  {% assign sorted_works_notes = works_notes | sort: 'date' | reverse %}
  <div class="note-index">
    {% for works_note in sorted_works_notes %}
      {% if works_note.published == false %}{% continue %}{% endif %}
      <div class="note-index-item">
        <span class="note-index-date">{% if works_note.date %}{{ works_note.date | date: "%-d %b %Y" }}{% endif %}</span>
        <a class="note-index-link" href="{{ works_note.url | relative_url }}">{{ works_note.title | default: works_note.slug }}</a>
      </div>
    {% endfor %}
  </div>
{% else %}
  <p>No curated notes yet.</p>
{% endif %}