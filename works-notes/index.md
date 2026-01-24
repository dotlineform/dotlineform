---
layout: default
title: Curated works
permalink: /works-notes/
---

<h1 class="visually-hidden">Works</h1>

{% assign sorted_works_notes = site.works_notes | sort: 'date' | reverse %}
<div class="note-index">

{% for works_note in sorted_works_notes %}
{% if works_note.published == false %}{% continue %}{% endif %}
<div class="note-index-item">
  <span class="note-index-date">{{ works_note.date | date: "%-d %b %Y" }}</span>
  <a class="note-index-link" href="{{ works_note.url | relative_url }}">{{ works_note.title | default: works_note.slug }}</a>
</div>
{% endfor %}
</div>