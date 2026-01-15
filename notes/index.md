---
layout: default
title: Notes
permalink: /notes/
---

# Notes

{% assign sorted_notes = site.notes | sort: 'date' | reverse %}

{% for note in sorted_notes %}
{% if note.published == false %}{% continue %}{% endif %}
- [{{ note.title | default: note.slug }}]({{ note.url | relative_url }}) ({{ note.date | date: "%Y-%m-%d" }})
{% endfor %}