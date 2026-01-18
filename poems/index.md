---
layout: default
title: Poems
permalink: /poems/
---

<h1 class="visually-hidden">Poems</h1>

{% assign sorted_poems = site.poems | sort: 'date' | reverse %}
<div class="poem-index">

{% for poem in sorted_poems %}
{% if poem.published == false %}{% continue %}{% endif %}
<div class="poem-index-item">
  <span class="poem-index-date">{{ poem.date | date: "%-d %b %Y" }}</span>
  <a class="poem-index-link" href="{{ poem.url | relative_url }}">{{ poem.title | default: poem.slug }}</a>
</div>
{% endfor %}
</div>