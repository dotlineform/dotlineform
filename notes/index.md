---
layout: default
title: Notes
permalink: /notes/
---

# Notes

{% assign sorted_notes = site.notes | sort: 'date' | reverse %}
<div class="note-index">

{% for note in sorted_notes %}
{% if note.published == false %}{% continue %}{% endif %}
<div class="note-index-item">
  <span class="note-index-date">{{ note.date | date: "%-d %b %Y" }}</span>
  <a class="note-index-link" href="{{ note.url | relative_url }}">{{ note.title | default: note.slug }}</a>
</div>
{% endfor %}
</div>