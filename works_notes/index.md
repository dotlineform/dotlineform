---
layout: default
title: Works
permalink: /works/
---

<h1 class="visually-hidden">Works</h1>

{% assign sorted_works = site.works | sort: 'date' | reverse %}
<div class="note-index">

{% for work in sorted_works %}
{% if work.published == false %}{% continue %}{% endif %}
<div class="note-index-item">
  <span class="note-index-date">{{ work.date | date: "%-d %b %Y" }}</span>
  <a class="note-index-link" href="{{ note.url | relative_url }}">{{ work.title | default: work.slug }}</a>
</div>
{% endfor %}
</div>